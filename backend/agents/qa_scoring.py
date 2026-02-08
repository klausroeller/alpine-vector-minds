"""QA Scoring Agent — evaluate conversation quality using the full QA rubric."""

import json
import logging

from openai import AsyncOpenAI

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from vector_db.embeddings import settings as embedding_settings

logger = logging.getLogger(__name__)

QA_SCORING_MODEL = "gpt-4o-mini"
QA_SCORING_TEMPERATURE = 0.1
QA_SCORING_MAX_TOKENS = 4096

# Full QA Evaluation Prompt based on the QA_Evaluation_Prompt rubric
QA_SCORING_SYSTEM_PROMPT = """\
You are a Quality Analyst (QA) reviewing:
1) a support interaction transcript (phone call or chat), AND/OR
2) the associated case/ticket record (Salesforce case fields: Description, Resolution, Notes, Category, etc.).

Your task:
- Evaluate the agent's performance and documentation quality using ONLY the evidence provided.
- Mark each parameter as Yes / No / N/A.
- If "No", you MUST cite Tracking Items verbatim from the Tracking Items Library (at the end) and include transcript/case evidence.
- Compute a weighted score out of 100%.

Accuracy Rules (Strict):
- Only evaluate based on transcript and/or case evidence. Do not assume missing steps happened.
- If there is not enough evidence to score a parameter, mark N/A.
- If you mark "No", include quotes/snippets from the transcript or case to justify why.
- Use Tracking Items verbatim when flagging failures (copy/paste from the Tracking Items Library).
- Do not fabricate missing data, customer details, IDs, or actions.

Evaluation Mode:
Determine what you are evaluating:
A) Interaction QA (Call/Chat) only
B) Case QA (Ticket) only
C) Both Interaction + Case

Scoring:
- If BOTH are available: Overall_Score = 70% Interaction_QA + 30% Case_QA
- If ONLY Interaction is available: Overall_Score = Interaction_QA (100%)
- If ONLY Case is available: Overall_Score = Case_QA (100%)

Autozero Rule (Critical):
- If Delivered_Expected_Outcome = "No" (Interaction QA), Interaction_QA score becomes 0%.
- If any Red Flag is triggered, Overall_Score becomes 0% (Autozero), regardless of other scores.

Interaction QA (Call/Chat) Parameters & Weights:
Customer Delight (50%):
1) Conversational & Professional (10%)
2) Engagement & Personalization (10%)
3) Tone & Pace (10%)
4) Language (10%)
5) Objection Handling / Conversation Control (10%)

Resolution Handling (50%):
6) Delivered Expected Outcome (10%, Autozero if "No")
7) Exhibit Critical Thinking (10%)
8) Educate & Accurately Handle Information (10%)
9) Effective Use of Resources (10%)
10) Call/Case Control & Timeliness (10%)

Case QA (Ticket) Parameters & Weights:
Case Documentation Quality (50%):
1) Clear Problem Summary (10%)
2) Captured Key Context (10%)
3) Action Log Completeness (10%)
4) Correct Categorization (10%)
5) Customer-Facing Clarity (10%)

Resolution Quality (50%):
6) Resolution is Specific & Reproducible (10%)
7) Uses Approved Process / Scripts When Required (10%)
8) Accuracy of Technical Content (10%)
9) References Knowledge Correctly (10%)
10) Timeliness & Ownership Signals (10%)

Red Flags (Autozero if any are "Yes"):
- Account Documentation Violation
- Payment Compliance / PCI Violation
- Data Integrity & Confidentiality Violation
- Misbehavior / Unprofessionalism

Tracking Items Library (Use Verbatim):

Interaction / Customer Delight:
- Did not greet the customer or introduce self
- Did not use professional closing
- Did not use customer name when available
- Did not confirm preferred contact method / callback details when needed
- Did not acknowledge customer concern or show empathy
- Talked over customer / interrupted frequently
- Unprofessional tone (rude, dismissive, sarcastic)
- Excessive filler words or unclear communication
- Spoke too fast / too slow without adapting
- Used jargon without explanation
- Did not set expectations or agenda for the call/chat
- Did not control the conversation (rambling / no structure)
- Did not address customer objections or concerns

Interaction / Resolution Handling:
- Did not confirm the issue or restate problem clearly
- Did not ask clarifying questions
- Did not verify key details before troubleshooting
- Provided incorrect or conflicting information
- Did not troubleshoot logically (random steps / guessing)
- Did not use available resources when appropriate (KB, scripts, peer help)
- Did not document or summarize steps taken during the interaction
- Did not confirm resolution with the customer
- Did not provide next steps or escalation path when unresolved
- Excessive hold time or delays without explanation
- Did not manage case ownership / follow-up expectations

Case / Documentation Quality:
- Case description is vague or incomplete
- Missing key context (module, error text, what changed, date/time)
- Steps taken not documented
- Resolution notes missing or unclear
- Incorrect category/subcategory selection
- Priority or tier does not match impact/urgency described
- Ticket not actionable for another agent
- Internal notes contain unnecessary or confusing content

Case / Resolution Quality:
- Resolution not reproducible / lacks verification steps
- Did not reference script when script-required
- Did not reference knowledge article when used
- Knowledge article should have been created or updated but was not
- Technical content appears inaccurate or unsupported by evidence
- No escalation notes when escalation is required
- No follow-up plan when issue is pending

Red Flags (Autozero):
- Included payment card data (PCI) in transcript or case notes
- Requested or stored sensitive authentication credentials
- Shared confidential customer data inappropriately
- Instructed unsafe data changes that risk data integrity
- Discriminatory, harassing, or otherwise unprofessional behavior

Respond ONLY with valid JSON (no markdown fences, no commentary). Use the exact output format below:

{
  "Evaluation_Mode": "Interaction|Case|Both",
  "Interaction_QA": {
    "Conversational_Professional": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Engagement_Personalization": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Tone_Pace": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Language": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Objection_Handling_Conversation_Control": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Delivered_Expected_Outcome": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Exhibit_Critical_Thinking": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Educate_Accurately_Handle_Information": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Effective_Use_of_Resources": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Call_Case_Control_Timeliness": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Final_Weighted_Score": "XX%"
  },
  "Case_QA": {
    "Clear_Problem_Summary": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Captured_Key_Context": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Action_Log_Completeness": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Correct_Categorization": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Customer_Facing_Clarity": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Resolution_Specific_Reproducible": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Uses_Approved_Process_Scripts_When_Required": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Accuracy_of_Technical_Content": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "References_Knowledge_Correctly": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Timeliness_Ownership_Signals": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Final_Weighted_Score": "XX%"
  },
  "Red_Flags": {
    "Account_Documentation_Violation": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Payment_Compliance_PCI_Violation": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Data_Integrity_Confidentiality_Violation": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""},
    "Misbehavior_Unprofessionalism": {"score": "Yes|No|N/A", "tracking_items": [], "evidence": ""}
  },
  "Business_Intelligence": {
    "Knowledge_Article_Attached": "Yes|No|N/A",
    "Screen_Recording_Available": "Yes|No|N/A",
    "PME_KCS_Attached": "Yes|No|N/A",
    "Work_Setup_WIO_WFH": "Yes|No|N/A",
    "Issues_IVR_IT_Tool_Audio": "Yes|No|N/A"
  },
  "Leader_Action_Required": "Yes|No",
  "Contact_Summary": "",
  "Case_Summary": "",
  "QA_Recommendation": "",
  "Overall_Weighted_Score": "XX%"
}\
"""


INTERACTION_QA_PARAMS = [
    "Conversational_Professional",
    "Engagement_Personalization",
    "Tone_Pace",
    "Language",
    "Objection_Handling_Conversation_Control",
    "Delivered_Expected_Outcome",
    "Exhibit_Critical_Thinking",
    "Educate_Accurately_Handle_Information",
    "Effective_Use_of_Resources",
    "Call_Case_Control_Timeliness",
]

CASE_QA_PARAMS = [
    "Clear_Problem_Summary",
    "Captured_Key_Context",
    "Action_Log_Completeness",
    "Correct_Categorization",
    "Customer_Facing_Clarity",
    "Resolution_Specific_Reproducible",
    "Uses_Approved_Process_Scripts_When_Required",
    "Accuracy_of_Technical_Content",
    "References_Knowledge_Correctly",
    "Timeliness_Ownership_Signals",
]

INTERACTION_WEIGHT = 0.70
CASE_WEIGHT = 0.30


def _section_score(section: dict, params: list[str]) -> float | None:
    """Compute a section score from individual Yes/No/N/A parameter values.

    Returns a float 0-100 or None if no scorable parameters exist.
    Each applicable (non-N/A) parameter has equal weight.
    """
    yes_count = 0
    applicable_count = 0
    for param in params:
        entry = section.get(param, {})
        if not isinstance(entry, dict):
            continue
        score = str(entry.get("score", "")).strip().lower()
        if score in ("yes", "no"):
            applicable_count += 1
            if score == "yes":
                yes_count += 1
        # N/A params are excluded from the denominator
    if applicable_count == 0:
        return None
    return (yes_count / applicable_count) * 100


def compute_overall_score(data: dict) -> float | None:
    """Compute the overall QA score server-side from individual parameter values.

    Applies the same rules as the prompt:
    - Both tracks: 70% Interaction + 30% Case
    - Single track: 100% of that track
    - Autozero if Delivered_Expected_Outcome = "No" (interaction becomes 0%)
    - Autozero if any red flag = "Yes" (overall becomes 0%)
    """
    # Check red flags first — any "Yes" means autozero
    red_flags = data.get("Red_Flags", {})
    for val in red_flags.values():
        if isinstance(val, dict) and str(val.get("score", "")).strip().lower() == "yes":
            return 0.0

    interaction_section = data.get("Interaction_QA", {})
    case_section = data.get("Case_QA", {})

    interaction_score = _section_score(interaction_section, INTERACTION_QA_PARAMS)
    case_score = _section_score(case_section, CASE_QA_PARAMS)

    # Autozero: if Delivered_Expected_Outcome is "No", interaction score becomes 0%
    deo = interaction_section.get("Delivered_Expected_Outcome", {})
    if isinstance(deo, dict) and str(deo.get("score", "")).strip().lower() == "no":
        interaction_score = 0.0

    if interaction_score is not None and case_score is not None:
        return interaction_score * INTERACTION_WEIGHT + case_score * CASE_WEIGHT
    if interaction_score is not None:
        return interaction_score
    if case_score is not None:
        return case_score
    return None


def parse_score_pct(value: str | int | float | None) -> float | None:
    """Parse 'XX%' or numeric to a float 0-100."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def extract_red_flags(data: dict) -> list[str]:
    """Extract red flag names where score is 'Yes'."""
    flags = []
    red_flags_section = data.get("Red_Flags", {})
    for key, val in red_flags_section.items():
        if isinstance(val, dict) and str(val.get("score", "")).lower() == "yes":
            flags.append(key.replace("_", " "))
    return flags


class QAScoringAgent(BaseAgent):
    """Score a support conversation using the full QA evaluation rubric."""

    def __init__(self) -> None:
        self.llm_client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Score a conversation.

        Expects a single user message with JSON containing:
        {
            "transcript": "...",
            "resolution": "...",
            "description": "...",
            "category": "...",
            "priority": "...",
            "module": "...",
            "product": "...",
            "root_cause": "...",
            "kb_article_id": "...",
            "script_id": "..."
        }
        """
        input_data = json.loads(messages[-1].content)
        transcript = input_data.get("transcript", "")
        resolution = input_data.get("resolution", "")
        description = input_data.get("description", "")
        category = input_data.get("category", "")
        priority = input_data.get("priority", "")
        module = input_data.get("module", "")
        product = input_data.get("product", "")
        root_cause = input_data.get("root_cause", "")
        kb_article_id = input_data.get("kb_article_id", "")
        script_id = input_data.get("script_id", "")

        # Build user message with all available evidence
        parts = []
        if transcript:
            parts.append(f"=== INTERACTION TRANSCRIPT ===\n{transcript}")
        if description or resolution or category:
            parts.append("=== CASE / TICKET DATA ===")
            if category:
                parts.append(f"Category: {category}")
            if priority:
                parts.append(f"Priority: {priority}")
            if product:
                parts.append(f"Product: {product}")
            if module:
                parts.append(f"Module: {module}")
            if description:
                parts.append(f"Description:\n{description}")
            if resolution:
                parts.append(f"Resolution:\n{resolution}")
            if root_cause:
                parts.append(f"Root Cause: {root_cause}")
            if kb_article_id:
                parts.append(f"KB Article ID: {kb_article_id}")
            if script_id:
                parts.append(f"Script ID: {script_id}")

        user_message = "\n\n".join(parts) if parts else "No evidence provided."

        try:
            completion = await self.llm_client.chat.completions.create(
                model=QA_SCORING_MODEL,
                messages=[
                    {"role": "system", "content": QA_SCORING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=QA_SCORING_TEMPERATURE,
                max_completion_tokens=QA_SCORING_MAX_TOKENS,
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
                        "Evaluation_Mode": "Both",
                        "Interaction_QA": {},
                        "Case_QA": {},
                        "Red_Flags": {},
                        "Overall_Weighted_Score": None,
                        "Contact_Summary": "QA scoring failed due to an internal error.",
                        "Case_Summary": "",
                        "QA_Recommendation": "",
                    }
                ),
                metadata={"model": QA_SCORING_MODEL, "error": True},
            )
