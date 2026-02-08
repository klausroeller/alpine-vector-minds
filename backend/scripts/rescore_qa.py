"""Re-score all conversations and compare old (LLM-reported) vs new (server-computed) scores."""

import asyncio
import json
import logging

from sqlalchemy import select

from agents import AgentMessage, QAScoringAgent
from agents.qa_scoring import compute_overall_score, extract_red_flags, parse_score_pct
from vector_db.database import async_session_maker, engine
from vector_db.models.conversation import Conversation
from vector_db.models.ticket import Ticket

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

CONCURRENCY = 5


async def rescore_all() -> None:
    async with async_session_maker() as session:
        convs = (await session.execute(select(Conversation).order_by(Conversation.id))).scalars().all()
        ticket_ids = {c.ticket_id for c in convs}
        tickets_map = {
            t.id: t
            for t in (await session.execute(select(Ticket).where(Ticket.id.in_(ticket_ids)))).scalars().all()
        }

        logger.info("Found %d conversations to re-score\n", len(convs))

        agent = QAScoringAgent()
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def score_one(conv: Conversation) -> tuple[str, float | None, float | None, float | None, list[str]]:
            old_score = conv.qa_score
            async with semaphore:
                ticket = tickets_map.get(conv.ticket_id)
                try:
                    input_data = json.dumps({
                        "transcript": conv.transcript or "",
                        "resolution": ticket.resolution if ticket else "",
                        "description": ticket.description if ticket else "",
                        "category": ticket.category if ticket else "",
                        "priority": ticket.priority if ticket else "",
                        "module": ticket.module if ticket else "",
                        "product": ticket.product if ticket else "",
                        "root_cause": ticket.root_cause if ticket else "",
                        "kb_article_id": ticket.kb_article_id if ticket else "",
                        "script_id": ticket.script_id if ticket else "",
                    })
                    result = await agent.run([AgentMessage(role="user", content=input_data)])
                    scores = json.loads(result.content)
                except Exception:
                    logger.exception("Failed to score %s", conv.id)
                    return conv.id, old_score, None, None, []

                llm_reported = parse_score_pct(scores.get("Overall_Weighted_Score"))
                computed = compute_overall_score(scores)
                red_flags = extract_red_flags(scores)

                # Store new scores
                from datetime import UTC, datetime

                conv.qa_score = computed if computed is not None else llm_reported
                conv.qa_scores_json = json.dumps(scores)
                conv.qa_red_flags = ",".join(red_flags)
                conv.qa_scored_at = datetime.now(UTC)

                return conv.id, old_score, llm_reported, computed, red_flags

        tasks = [score_one(c) for c in convs]
        results = await asyncio.gather(*tasks)

        # Print comparison table
        logger.info("%-12s  %10s  %10s  %10s  %s", "Conv ID", "Old Score", "LLM Score", "Computed", "Red Flags")
        logger.info("-" * 80)

        mismatches = 0
        changes = 0
        for conv_id, old_score, llm_reported, computed, red_flags in results:
            old_str = f"{old_score:.1f}" if old_score is not None else "N/A"
            llm_str = f"{llm_reported:.1f}" if llm_reported is not None else "N/A"
            comp_str = f"{computed:.1f}" if computed is not None else "N/A"
            flags_str = ", ".join(red_flags) if red_flags else "-"

            marker = ""
            if computed is not None and llm_reported is not None and abs(computed - llm_reported) > 0.1:
                marker = " *** MISMATCH"
                mismatches += 1
            if old_score is not None and computed is not None and abs(old_score - computed) > 0.1:
                changes += 1

            logger.info("%-12s  %10s  %10s  %10s  %s%s", conv_id, old_str, llm_str, comp_str, flags_str, marker)

        logger.info("-" * 80)
        logger.info("Total: %d conversations", len(results))
        logger.info("LLM vs Computed mismatches: %d", mismatches)
        logger.info("Old vs New score changes: %d", changes)

        await session.commit()
        logger.info("\nScores saved to database.")

    await engine.dispose()


def main() -> None:
    asyncio.run(rescore_all())


if __name__ == "__main__":
    main()
