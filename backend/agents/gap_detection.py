import json
import logging
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from api.core.constants import KB_GAP_THRESHOLD
from vector_db.embeddings import EmbeddingService
from vector_db.embeddings import settings as embedding_settings
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

GAP_DETECTION_SYSTEM_PROMPT = """\
You are a knowledge gap detector for RealPage PropertySuite Affordable support.

You are given a resolved support ticket and the closest matching existing KB article.

Determine if the ticket resolution contains NEW knowledge that should be captured
in a KB article. Consider:
- Does the existing KB article cover this exact scenario adequately?
- Is the resolution substantially different from the existing article?
- Would a new article help future support agents handle similar cases?
- Does the resolution contain specific steps or insights not in the KB?

Respond ONLY with valid JSON (no markdown fences):
{"gap_detected": true/false, "gap_description": "what knowledge is missing", "suggested_title": "title for new KB article"}\
"""


class GapDetectionAgent(BaseAgent):
    """Detect knowledge gaps in resolved tickets.

    Given a resolved ticket, determine whether its resolution represents
    new knowledge not yet captured in the existing knowledge base.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        search_service: VectorSearchService | None = None,
        gap_threshold: float = KB_GAP_THRESHOLD,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        self.search_service = search_service or VectorSearchService(db)
        self.llm_client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)
        self.chat_model = embedding_settings.OPENAI_CHAT_MODEL
        self.gap_threshold = gap_threshold

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Detect whether a ticket's resolution has a knowledge gap.

        Expects a single user message with JSON containing:
        {
            "ticket_description": "...",
            "ticket_resolution": "...",
            "ticket_category": "...",
            "ticket_id": "..."
        }
        """
        input_data = json.loads(messages[-1].content)
        description = input_data.get("ticket_description", "")
        resolution = input_data.get("ticket_resolution", "")
        category = input_data.get("ticket_category", "")
        ticket_id = input_data.get("ticket_id", "")

        # Step 1: Embed the ticket description + resolution
        embed_text = f"{description}\n{resolution}"
        query_embedding = await self.embedding_service.embed(embed_text)

        # Step 2: Find best matching KB article
        best_match = await self.search_service.find_best_kb_match(query_embedding)

        # Step 3: Check similarity threshold
        if best_match and best_match["similarity_score"] >= self.gap_threshold:
            return AgentResponse(
                content=json.dumps({
                    "gap_detected": False,
                    "gap_description": (
                        f"Existing KB article '{best_match['title']}' "
                        f"(similarity: {best_match['similarity_score']:.3f}) "
                        f"covers this scenario."
                    ),
                    "suggested_title": None,
                    "best_match_id": best_match["id"],
                    "best_match_similarity": best_match["similarity_score"],
                }),
                metadata={
                    "ticket_id": ticket_id,
                    "threshold": self.gap_threshold,
                    "best_match_similarity": best_match["similarity_score"],
                },
            )

        # Step 4: Below threshold — confirm gap via LLM
        best_match_context = (
            f"Title: {best_match['title']}\n"
            f"Preview: {best_match['content_preview']}\n"
            f"Similarity: {best_match['similarity_score']:.3f}"
            if best_match
            else "No matching KB article found."
        )

        gap_result = await self._confirm_gap_with_llm(
            description=description,
            resolution=resolution,
            category=category,
            best_match_context=best_match_context,
        )

        similarity = best_match["similarity_score"] if best_match else 0.0

        return AgentResponse(
            content=json.dumps({
                "gap_detected": gap_result["gap_detected"],
                "gap_description": gap_result.get("gap_description", ""),
                "suggested_title": gap_result.get("suggested_title"),
                "best_match_id": best_match["id"] if best_match else None,
                "best_match_similarity": similarity,
            }),
            metadata={
                "ticket_id": ticket_id,
                "threshold": self.gap_threshold,
                "best_match_similarity": similarity,
                "llm_confirmed": True,
            },
        )

    async def _confirm_gap_with_llm(
        self,
        description: str,
        resolution: str,
        category: str,
        best_match_context: str,
    ) -> dict[str, Any]:
        """Use LLM to confirm whether there's a real knowledge gap."""
        user_message = (
            f"Ticket Category: {category}\n\n"
            f"Ticket Description:\n{description}\n\n"
            f"Ticket Resolution:\n{resolution}\n\n"
            f"Closest Existing KB Article:\n{best_match_context}"
        )

        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": GAP_DETECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_completion_tokens=300,
            )
            raw = completion.choices[0].message.content or "{}"
            raw = strip_markdown_fences(raw)
            return json.loads(raw)
        except Exception:
            logger.exception("LLM gap confirmation failed, assuming gap exists")
            return {
                "gap_detected": True,
                "gap_description": (
                    f"No existing KB match above {self.gap_threshold} threshold "
                    f"for {category} issue; LLM confirmation failed."
                ),
                "suggested_title": f"Resolving {category} Issues",
            }
