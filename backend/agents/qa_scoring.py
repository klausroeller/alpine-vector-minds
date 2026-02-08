"""QA Scoring Agent — evaluate conversation quality against a 6-category rubric."""

import json
import logging

from openai import AsyncOpenAI

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from vector_db.embeddings import settings as embedding_settings

logger = logging.getLogger(__name__)

QA_SCORING_MODEL = "gpt-4o-mini"
QA_SCORING_TEMPERATURE = 0.1

QA_SCORING_SYSTEM_PROMPT = """\
You are a QA evaluator for RealPage PropertySuite Affordable customer support.

Score the following support interaction on 6 weighted categories using 0-100 scale:

1. **Greeting & Empathy** (10%) — Professional opening, empathetic language, active listening
2. **Issue Identification** (15%) — Correctly identified the root cause, asked clarifying questions
3. **Troubleshooting Quality** (20%) — Systematic diagnosis, followed standard procedures, efficient process
4. **Resolution Accuracy** (25%) — Correct fix applied, verified resolution, addressed all aspects
5. **Documentation Quality** (15%) — Clear notes, proper categorization, actionable follow-up items
6. **Compliance & Safety** (15%) — Data privacy respected, proper authorization checks, escalation when needed

**Auto-Zero Red Flags** — If ANY of these are present, set overall_score to 0:
- Shared credentials or passwords in plaintext
- Skipped required identity verification
- Made unauthorized changes to financial data
- Gave medical/legal advice outside scope

Respond ONLY with valid JSON (no markdown fences):
{
  "overall_score": <weighted average 0-100 or 0 if red flag>,
  "categories": {
    "greeting_empathy": {"score": <0-100>, "weight": 0.10, "feedback": "<1 sentence>"},
    "issue_identification": {"score": <0-100>, "weight": 0.15, "feedback": "<1 sentence>"},
    "troubleshooting_quality": {"score": <0-100>, "weight": 0.20, "feedback": "<1 sentence>"},
    "resolution_accuracy": {"score": <0-100>, "weight": 0.25, "feedback": "<1 sentence>"},
    "documentation_quality": {"score": <0-100>, "weight": 0.15, "feedback": "<1 sentence>"},
    "compliance_safety": {"score": <0-100>, "weight": 0.15, "feedback": "<1 sentence>"}
  },
  "red_flags": ["<flag description if any>"],
  "summary": "<2-3 sentence overall assessment>"
}\
"""


class QAScoringAgent(BaseAgent):
    """Score a support conversation against a 6-category QA rubric."""

    def __init__(self) -> None:
        self.llm_client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Score a conversation.

        Expects a single user message with JSON containing:
        {
            "transcript": "...",
            "resolution": "...",
            "category": "...",
            "priority": "..."
        }
        """
        input_data = json.loads(messages[-1].content)
        transcript = input_data.get("transcript", "")
        resolution = input_data.get("resolution", "")
        category = input_data.get("category", "")
        priority = input_data.get("priority", "")

        user_message = (
            f"Category: {category}\n"
            f"Priority: {priority}\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Resolution:\n{resolution}"
        )

        try:
            completion = await self.llm_client.chat.completions.create(
                model=QA_SCORING_MODEL,
                messages=[
                    {"role": "system", "content": QA_SCORING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=QA_SCORING_TEMPERATURE,
                max_completion_tokens=600,
            )
            raw = completion.choices[0].message.content or "{}"
            raw = strip_markdown_fences(raw)
            result = json.loads(raw)

            return AgentResponse(
                content=json.dumps(result),
                metadata={"model": QA_SCORING_MODEL},
            )
        except Exception:
            logger.exception("QA scoring failed")
            return AgentResponse(
                content=json.dumps(
                    {
                        "overall_score": None,
                        "categories": {},
                        "red_flags": [],
                        "summary": "QA scoring failed due to an internal error.",
                    }
                ),
                metadata={"model": QA_SCORING_MODEL, "error": True},
            )
