import json
import logging
import time
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from api.core.constants import ENABLE_RERANKING, RERANK_CANDIDATE_COUNT, SEARCH_RESULT_LIMIT
from vector_db.embeddings import EmbeddingService
from vector_db.embeddings import settings as embedding_settings
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """\
You are a support triage classifier for RealPage PropertySuite Affordable.
Given a customer support question, classify what type of resource would best answer it,
and produce a concise, search-optimized rewrite of the question.

Categories:
- SCRIPT: The question describes a backend data issue that requires a SQL fix script.
  Indicators: "backend data", "sync", "invalid reference", "Tier 3", data fix needed,
  database correction, data inconsistency, backend voucher, backend fix,
  "remediation script", "what script should we run".
- KB: The question asks about a workflow, how-to, configuration, or best practice.
  Indicators: "how to", "where do I", "steps to", general guidance needed,
  workflow question, configuration help, best practice, "explain how to",
  "common mistakes", troubleshooting guidance.
- TICKET_RESOLUTION: The question asks about how a specific past issue was resolved,
  or requests precedent from previous cases.
  Indicators: "how was this resolved", "similar cases", "what was the resolution",
  "past incident", "precedent", asks for resolution steps from prior tickets.

Examples:

User: "In PropertySuite Affordable, we're seeing a workflow block in Accounting / Date Advance that's stopping move-ins. It appears related to backend data in Haprequest data. What Tier 3 remediation script/process should Support run?"
Answer: {"answer_type": "SCRIPT", "confidence": 0.95, "reasoning": "Mentions backend data issue and asks for a Tier 3 remediation script", "search_query": "Haprequest backend data fix Advance Property Date move-in block remediation script"}

User: "Can you explain how to handle: Screening Task on Move-In Checklist Appears as Optional Despite Being Set as Required in PropertySuite Affordable and what common mistakes cause issues?"
Answer: {"answer_type": "KB", "confidence": 0.90, "reasoning": "Asks for explanation and common mistakes — guidance/how-to question", "search_query": "Screening Task Move-In Checklist optional vs required configuration"}

User: "A user can't complete a General report in General. A report or form output doesn't look right (site: Meadow Pointe). What was the resolution in similar cases?"
Answer: {"answer_type": "TICKET_RESOLUTION", "confidence": 0.85, "reasoning": "Asks for resolution from similar past cases — precedent lookup", "search_query": "General report form output incorrect resolution Meadow Pointe"}

Rules for search_query:
- Remove filler words, pleasantries, and redundant context
- Keep product names, module names, error messages, and technical terms
- Expand acronyms if possible (e.g., "APD" → "Advance Property Date")
- Aim for 8-15 keywords that would match relevant documents

Respond ONLY with valid JSON (no markdown fences):
{"answer_type": "SCRIPT|KB|TICKET_RESOLUTION", "confidence": 0.0-1.0, "reasoning": "brief explanation", "search_query": "concise keyword-rich search query"}\
"""


class TriageAgent(BaseAgent):
    """Classify a support question and retrieve the best matching resources."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        search_service: VectorSearchService | None = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        self.search_service = search_service or VectorSearchService(db)
        self.llm_client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)
        self.triage_model = "gpt-4o-mini"

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Classify the question and retrieve relevant resources.

        Expects a single user message containing the question text.
        """
        start_time = time.perf_counter()
        question = messages[-1].content

        # Step 1: Classify the question via LLM
        classification = await self._classify(question)

        # Step 2: Embed the rewritten search query (better than raw question)
        search_query = classification["search_query"]
        query_embedding = await self.embedding_service.embed(search_query)

        # Step 3: Search the primary pool
        primary_results, search_ms = await self.search_service.search_all(
            query_embedding,
            answer_type=classification["answer_type"],
            limit=SEARCH_RESULT_LIMIT,
            raw_question=question,
        )

        # Step 4: Search a secondary pool for supplementary results
        secondary_type = _secondary_pool(classification["answer_type"])
        secondary_results, _ = await self.search_service.search_all(
            query_embedding,
            answer_type=secondary_type,
            limit=5,
            raw_question=question,
        )

        # Combine results with source_type tagging
        ranked_results = _build_ranked_results(
            primary_results,
            classification["answer_type"],
            secondary_results,
            secondary_type,
        )

        # Step 5: LLM reranking (optional)
        if ENABLE_RERANKING and ranked_results:
            ranked_results = await self._rerank(question, ranked_results)

        total_ms = (time.perf_counter() - start_time) * 1000

        response_payload: dict[str, Any] = {
            "classification": classification,
            "results": ranked_results,
        }

        return AgentResponse(
            content=json.dumps(response_payload),
            metadata={
                "search_time_ms": round(search_ms, 1),
                "total_time_ms": round(total_ms, 1),
                "primary_pool": classification["answer_type"],
                "secondary_pool": secondary_type,
                "result_count": len(ranked_results),
                "search_query": search_query,
            },
        )

    async def _rerank(
        self, question: str, candidates: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Use LLM to rerank candidates by relevance to the question."""
        to_rerank = candidates[:RERANK_CANDIDATE_COUNT]
        remainder = candidates[RERANK_CANDIDATE_COUNT:]

        # Build a compact preview of each candidate for the LLM
        previews = []
        for c in to_rerank:
            title = c.get("title", "")[:120]
            preview = c.get("content_preview", "")[:200]
            previews.append(f"[{c['id']}] {title} — {preview}")

        prompt = (
            "Given the support question and candidate results below, "
            "return the IDs in order of relevance (most relevant first). "
            'Return ONLY a JSON array of IDs, e.g. ["KB-123", "SCRIPT-45"].\n\n'
            f"Question: {question}\n\n"
            "Candidates:\n" + "\n".join(previews)
        )

        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.triage_model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=500,
            )
            raw = strip_markdown_fences(completion.choices[0].message.content or "[]")
            ranked_ids = json.loads(raw)

            if not isinstance(ranked_ids, list):
                return candidates

            # Rebuild ordered list from LLM ranking
            id_to_candidate = {c["id"]: c for c in to_rerank}
            reranked = []
            for doc_id in ranked_ids:
                if doc_id in id_to_candidate:
                    reranked.append(id_to_candidate.pop(doc_id))

            # Append any candidates the LLM missed
            for c in to_rerank:
                if c["id"] in id_to_candidate:
                    reranked.append(c)

            # Re-number ranks
            for i, item in enumerate(reranked + remainder, start=1):
                item["rank"] = i

            return reranked + remainder

        except Exception:
            logger.exception("Reranking failed, keeping original order")
            return candidates

    async def _classify(self, question: str) -> dict[str, Any]:
        """Classify question into SCRIPT / KB / TICKET_RESOLUTION and rewrite query."""
        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.triage_model,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                max_completion_tokens=300,
            )
            raw = completion.choices[0].message.content or "{}"
            raw = strip_markdown_fences(raw)
            parsed = json.loads(raw)
            # Validate answer_type
            if parsed.get("answer_type") not in ("SCRIPT", "KB", "TICKET_RESOLUTION"):
                parsed["answer_type"] = "KB"
                parsed["confidence"] = 0.5
            return {
                "answer_type": parsed["answer_type"],
                "confidence": float(parsed.get("confidence", 0.5)),
                "reasoning": parsed.get("reasoning", ""),
                "search_query": parsed.get("search_query", question),
            }
        except Exception:
            logger.exception("Classification failed, defaulting to KB")
            return {
                "answer_type": "KB",
                "confidence": 0.3,
                "reasoning": "Classification failed — falling back to KB search.",
                "search_query": question,
            }


def _secondary_pool(primary: str) -> str:
    """Pick a secondary search pool for supplementary results."""
    if primary == "SCRIPT":
        return "KB"
    if primary == "KB":
        return "SCRIPT"
    return "KB"  # TICKET_RESOLUTION → KB as secondary


def _build_ranked_results(
    primary: list[dict[str, Any]],
    primary_type: str,
    secondary: list[dict[str, Any]],
    secondary_type: str,
) -> list[dict[str, Any]]:
    """Merge primary and secondary results into a ranked list."""
    ranked: list[dict[str, Any]] = []
    for i, r in enumerate(primary, start=1):
        ranked.append(
            {
                "rank": i,
                "source_type": primary_type,
                **r,
            }
        )
    offset = len(primary)
    for i, r in enumerate(secondary, start=1):
        ranked.append(
            {
                "rank": offset + i,
                "source_type": secondary_type,
                **r,
            }
        )
    return ranked
