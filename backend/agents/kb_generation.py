import json
import logging
from typing import Any

from openai import AsyncOpenAI

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from vector_db.embeddings import settings as embedding_settings

logger = logging.getLogger(__name__)

KB_GENERATION_SYSTEM_PROMPT = """\
You are a technical writer for RealPage PropertySuite Affordable support.
Generate a knowledge base article from the provided resolved support ticket.

Requirements:
- Title: Clear, searchable title describing the issue and resolution
- Body structure:
  1. Problem description (what the user experiences)
  2. Root cause (why it happens)
  3. Resolution steps (numbered, actionable)
  4. Related information (category, module, affected roles)
- Use the conversation transcript for context on the user's experience
- If a Tier 3 script was used, reference it but don't include raw SQL
- Keep the language professional and consistent with existing KB articles
- Use placeholders from the placeholder dictionary where appropriate

Respond ONLY with valid JSON (no markdown fences):
{"title": "Article Title", "body": "Full article text", "category": "Category Name"}\
"""


class KBGenerationAgent(BaseAgent):
    """Generate draft KB articles from resolved tickets.

    Takes ticket + conversation + script data and produces a well-structured
    knowledge base article ready for human review.
    """

    def __init__(self) -> None:
        self.llm_client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)
        self.chat_model = embedding_settings.OPENAI_CHAT_MODEL

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Generate a draft KB article.

        Expects a single user message with JSON containing:
        {
            "ticket_id": "CS-...",
            "ticket_description": "...",
            "ticket_resolution": "...",
            "ticket_category": "...",
            "ticket_module": "...",
            "ticket_root_cause": "...",
            "conversation_transcript": "..." (optional),
            "script_title": "..." (optional),
            "script_id": "..." (optional),
            "suggested_title": "..." (optional, from gap detection)
        }
        """
        input_data = json.loads(messages[-1].content)

        article = await self._generate_article(input_data)

        return AgentResponse(
            content=json.dumps(article),
            metadata={
                "ticket_id": input_data.get("ticket_id", ""),
                "generated": True,
            },
        )

    async def _generate_article(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate the KB article via LLM."""
        user_message = self._build_prompt(data)

        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": KB_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_completion_tokens=1500,
            )
            raw = completion.choices[0].message.content or "{}"
            raw = strip_markdown_fences(raw)
            parsed = json.loads(raw)
            return {
                "title": parsed.get("title") or data.get("suggested_title") or "Untitled",
                "body": parsed.get("body") or "",
                "category": parsed.get("category") or data.get("ticket_category") or "",
            }
        except Exception:
            logger.exception("KB article generation failed, returning fallback")
            return self._fallback_article(data)

    def _build_prompt(self, data: dict[str, Any]) -> str:
        """Build the user prompt from ticket data."""
        parts = [
            f"Ticket ID: {data.get('ticket_id', 'N/A')}",
            f"Category: {data.get('ticket_category', 'N/A')}",
            f"Module: {data.get('ticket_module', 'N/A')}",
            f"Root Cause: {data.get('ticket_root_cause', 'N/A')}",
            "",
            "Description:",
            data.get("ticket_description", "No description provided."),
            "",
            "Resolution:",
            data.get("ticket_resolution", "No resolution provided."),
        ]

        transcript = data.get("conversation_transcript")
        if transcript:
            parts.extend(["", "Conversation Transcript:", transcript])

        script_title = data.get("script_title")
        script_id = data.get("script_id")
        if script_title:
            parts.extend(
                [
                    "",
                    f"Tier 3 Script Used: {script_title} ({script_id or 'N/A'})",
                ]
            )

        suggested = data.get("suggested_title")
        if suggested:
            parts.extend(["", f"Suggested Title: {suggested}"])

        return "\n".join(parts)

    def _fallback_article(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate a simple fallback article when LLM fails."""
        category = data.get("ticket_category", "General")
        description = data.get("ticket_description", "")
        resolution = data.get("ticket_resolution", "")

        title = data.get("suggested_title") or f"Resolving {category} Issues"
        body = f"Problem Description:\n{description}\n\nResolution:\n{resolution}"
        return {"title": title, "body": body, "category": category}
