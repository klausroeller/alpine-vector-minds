import json
import logging
import time
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from api.core.constants import SEARCH_RESULT_LIMIT
from vector_db.embeddings import EmbeddingService
from vector_db.embeddings import settings as embedding_settings
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """\
You are a support triage classifier for RealPage PropertySuite Affordable.
Given a customer support question, classify what type of resource would best answer it.

Categories:
- SCRIPT: The question describes a backend data issue that requires a SQL fix script.
  Indicators: "backend data", "sync", "invalid reference", "Tier 3", data fix needed,
  database correction, data inconsistency, backend voucher, backend fix.
- KB: The question asks about a workflow, how-to, configuration, or best practice.
  Indicators: "how to", "where do I", "steps to", general guidance needed,
  workflow question, configuration help, best practice.
- TICKET_RESOLUTION: The question asks about how a specific past issue was resolved.
  Indicators: references a specific scenario, asks for precedent, resolution steps,
  "how was this resolved", past incident.

Respond ONLY with valid JSON (no markdown fences):
{"answer_type": "SCRIPT|KB|TICKET_RESOLUTION", "confidence": 0.0-1.0, "reasoning": "brief explanation"}\
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
        self.chat_model = embedding_settings.OPENAI_CHAT_MODEL

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Classify the question and retrieve relevant resources.

        Expects a single user message containing the question text.
        """
        start_time = time.perf_counter()
        question = messages[-1].content

        # Step 1: Classify the question via LLM
        classification = await self._classify(question)

        # Step 2: Embed the question
        query_embedding = await self.embedding_service.embed(question)

        # Step 3: Search the primary pool
        primary_results, search_ms = await self.search_service.search_all(
            query_embedding,
            answer_type=classification["answer_type"],
            limit=SEARCH_RESULT_LIMIT,
        )

        # Step 4: Search a secondary pool for supplementary results
        secondary_type = _secondary_pool(classification["answer_type"])
        secondary_results, _ = await self.search_service.search_all(
            query_embedding,
            answer_type=secondary_type,
            limit=5,
        )

        # Combine results with source_type tagging
        ranked_results = _build_ranked_results(
            primary_results, classification["answer_type"],
            secondary_results, secondary_type,
        )

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
            },
        )

    async def _classify(self, question: str) -> dict[str, Any]:
        """Classify question into SCRIPT / KB / TICKET_RESOLUTION."""
        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                max_completion_tokens=200,
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
            }
        except Exception:
            logger.exception("Classification failed, defaulting to KB")
            return {
                "answer_type": "KB",
                "confidence": 0.3,
                "reasoning": "Classification failed — falling back to KB search.",
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
        ranked.append({
            "rank": i,
            "source_type": primary_type,
            **r,
        })
    offset = len(primary)
    for i, r in enumerate(secondary, start=1):
        ranked.append({
            "rank": offset + i,
            "source_type": secondary_type,
            **r,
        })
    return ranked
