import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage
from agents.deep_research import DeepResearchAgent
from agents.triage import TriageAgent
from api.v1.auth import get_current_user
from api.v1.schemas.copilot import (
    AIAnswer,
    Classification,
    CopilotAskRequest,
    CopilotAskResponse,
    CopilotResearchRequest,
    CopilotResearchResponse,
    EvaluationStepResponse,
    EvidenceItem,
    ProvenanceInfo,
    RelatedResource,
    ResearchReport,
    SearchResult,
    SubQueryInfo,
)
from vector_db.database import get_db
from vector_db.embeddings import EmbeddingService
from vector_db.embeddings import settings as embedding_settings
from vector_db.models.copilot_feedback import CopilotFeedback
from vector_db.models.kb_lineage import KBLineage
from vector_db.models.question import Question
from vector_db.models.user import User
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

_ANSWER_MODEL = "gpt-4o-mini"

_ANSWER_SYSTEM_PROMPT = """\
You are a support copilot for RealPage PropertySuite Affordable.
Given a support agent's question and the top matching resource from the knowledge base, \
write a concise, actionable answer the agent can use immediately.

Rules:
- Be direct and practical — the agent needs to act fast
- Reference source IDs in square brackets, e.g. [KB-123] or [SCRIPT-45]
- For KB articles: summarize the key steps or information
- For scripts: explain what the script does, list required placeholders, and note any prerequisites
- For ticket resolutions: summarize what was done to resolve the issue
- Keep the answer to 2-4 sentences
- Do NOT add disclaimers or caveats\
"""


async def _generate_ai_answer(
    question: str, results: list[SearchResult],
) -> AIAnswer | None:
    """Generate a synthesized answer from the top search results."""
    if not results:
        return None

    top = results[0]
    context = f"Source: [{top.source_id}] {top.title}\nType: {top.source_type}\n\n{top.content_preview}"

    # Include second result if available and high-scoring
    source_ids = [top.source_id]
    if len(results) > 1 and results[1].similarity_score > 0.7:
        r2 = results[1]
        context += f"\n\n---\nSource: [{r2.source_id}] {r2.title}\nType: {r2.source_type}\n\n{r2.content_preview}"
        source_ids.append(r2.source_id)

    try:
        client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model=_ANSWER_MODEL,
            messages=[
                {"role": "system", "content": _ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}\n\n{context}"},
            ],
            max_tokens=300,
        )
        text = completion.choices[0].message.content or ""
        return AIAnswer(text=text.strip(), source_ids=source_ids)
    except Exception:
        logger.exception("AI answer generation failed")
        return None

router = APIRouter()

# Map agent-internal answer_type labels to frontend source_type values
_SOURCE_TYPE_MAP: dict[str, str] = {
    "SCRIPT": "script",
    "KB": "kb_article",
    "TICKET_RESOLUTION": "ticket",
}


async def _get_provenance(db: AsyncSession, article_id: str) -> ProvenanceInfo | None:
    """Fetch provenance info from kb_lineage for a KB article."""
    result = await db.execute(select(KBLineage).where(KBLineage.kb_article_id == article_id))
    rows = result.scalars().all()
    if not rows:
        return None

    created_from_ticket = None
    created_from_conversation = None
    references_script = None

    for row in rows:
        if row.relationship == "CREATED_FROM" and row.source_id:
            if row.source_id.startswith("CS-"):
                created_from_ticket = row.source_id
            elif row.source_id.startswith("CONV-"):
                created_from_conversation = row.source_id
        elif (
            row.relationship == "REFERENCES"
            and row.source_id
            and row.source_id.startswith("SCRIPT-")
        ):
            references_script = row.source_id

    if not any([created_from_ticket, created_from_conversation, references_script]):
        return None

    return ProvenanceInfo(
        created_from_ticket=created_from_ticket,
        created_from_conversation=created_from_conversation,
        references_script=references_script,
    )


async def _build_search_results(
    db: AsyncSession, raw_results: list[dict], start_rank: int = 1
) -> list[SearchResult]:
    """Convert raw agent results to SearchResult models with provenance enrichment."""
    results: list[SearchResult] = []
    for i, r in enumerate(raw_results):
        raw_type = r.get("source_type", "")
        source_type = _SOURCE_TYPE_MAP.get(raw_type, raw_type)
        source_id = r.get("id", "")

        provenance = None
        if source_type == "kb_article":
            provenance = await _get_provenance(db, source_id)

        results.append(
            SearchResult(
                rank=r.get("rank", start_rank + i),
                source_type=source_type,
                source_id=source_id,
                title=r.get("title", ""),
                content_preview=r.get("content_preview", ""),
                similarity_score=r.get("similarity_score", 0.0),
                category=r.get("category"),
                placeholders=r.get("placeholders"),
                provenance=provenance,
            )
        )
    return results


@router.post("/ask", response_model=CopilotAskResponse)
async def copilot_ask(
    request: CopilotAskRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopilotAskResponse:
    embedding_service = EmbeddingService()
    search_service = VectorSearchService(db)
    triage_agent = TriageAgent(db, embedding_service, search_service)

    response = await triage_agent.run([AgentMessage(role="user", content=request.question)])

    payload = json.loads(response.content)
    classification_data = payload["classification"]
    raw_results = payload.get("results", [])

    classification = Classification(
        answer_type=classification_data["answer_type"],
        confidence=classification_data["confidence"],
        reasoning=classification_data["reasoning"],
    )

    results = await _build_search_results(db, raw_results)

    ai_answer = await _generate_ai_answer(request.question, results)

    return CopilotAskResponse(
        classification=classification,
        ai_answer=ai_answer,
        results=results,
        metadata=response.metadata,
    )


@router.post("/research", response_model=CopilotResearchResponse)
async def copilot_research(
    request: CopilotResearchRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopilotResearchResponse:
    embedding_service = EmbeddingService()
    search_service = VectorSearchService(db)
    agent = DeepResearchAgent(db, embedding_service, search_service)

    response = await agent.run([AgentMessage(role="user", content=request.question)])
    payload = json.loads(response.content)
    mode = payload.get("mode", "research")

    if mode == "simple":
        classification_data = payload.get("classification", {})
        classification = Classification(
            answer_type=classification_data.get("answer_type", "KB"),
            confidence=classification_data.get("confidence", 0.5),
            reasoning=classification_data.get("reasoning", ""),
        )
        results = await _build_search_results(db, payload.get("results", []))

        return CopilotResearchResponse(
            mode="simple",
            classification=classification,
            results=results,
            metadata=response.metadata,
        )

    # Research mode
    raw_report = payload.get("report", {})
    report = ResearchReport(
        summary=raw_report.get("summary", ""),
        evidence=[
            EvidenceItem(
                source_id=e.get("source_id", ""),
                source_type=_SOURCE_TYPE_MAP.get(
                    e.get("source_type", ""), e.get("source_type", "")
                ),
                title=e.get("title", ""),
                relevance=e.get("relevance", ""),
                content_preview=e.get("content_preview", ""),
            )
            for e in raw_report.get("evidence", [])
        ],
        related_resources=[
            RelatedResource(
                source_id=r.get("source_id", ""),
                source_type=_SOURCE_TYPE_MAP.get(
                    r.get("source_type", ""), r.get("source_type", "")
                ),
                title=r.get("title", ""),
                why_relevant=r.get("why_relevant", ""),
            )
            for r in raw_report.get("related_resources", [])
        ],
    )

    sub_queries = [
        SubQueryInfo(
            query=sq.get("query", ""),
            pool=sq.get("pool", ""),
            aspect=sq.get("aspect", ""),
        )
        for sq in payload.get("sub_queries", [])
    ]

    return CopilotResearchResponse(
        mode="research",
        report=report,
        sub_queries=sub_queries,
        metadata=response.metadata,
    )


@router.get("/evaluate", response_model=EvaluationStepResponse)
async def copilot_evaluate(
    index: int = Query(..., ge=0),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationStepResponse:
    # Fetch all ground-truth questions in deterministic order
    result = await db.execute(select(Question).order_by(Question.id))
    questions = result.scalars().all()

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ground-truth questions found in database",
        )

    total = len(questions)

    if index >= total:
        return EvaluationStepResponse(done=True, total=total)

    q = questions[index]
    answer_type = q.answer_type or "UNKNOWN"

    try:
        response = await copilot_ask(
            CopilotAskRequest(question=q.question_text),
            _current_user,
            db,
        )
        classified_type = response.classification.answer_type
        result_ids = [r.source_id for r in response.results]

        classification_correct = classified_type == answer_type

        h1 = bool(q.target_id and q.target_id in result_ids[:1])
        h5 = bool(q.target_id and q.target_id in result_ids[:5])
        h10 = bool(q.target_id and q.target_id in result_ids[:10])

        return EvaluationStepResponse(
            done=False,
            total=total,
            index=index,
            question_id=str(q.id),
            answer_type=answer_type,
            difficulty=q.difficulty,
            classified_type=classified_type,
            classification_correct=classification_correct,
            target_id=q.target_id,
            hit_at_1=h1,
            hit_at_5=h5,
            hit_at_10=h10,
            error=False,
        )
    except Exception:
        logger.exception("Evaluation failed for question %s", q.id)
        return EvaluationStepResponse(
            done=False,
            total=total,
            index=index,
            question_id=str(q.id),
            answer_type=answer_type,
            difficulty=q.difficulty,
            error=True,
        )


@router.get("/evaluate-research", response_model=EvaluationStepResponse)
async def copilot_evaluate_research(
    index: int = Query(..., ge=0),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationStepResponse:
    result = await db.execute(select(Question).order_by(Question.id))
    questions = result.scalars().all()

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ground-truth questions found in database",
        )

    total = len(questions)

    if index >= total:
        return EvaluationStepResponse(done=True, total=total)

    q = questions[index]
    answer_type = q.answer_type or "UNKNOWN"

    try:
        response = await copilot_research(
            CopilotResearchRequest(question=q.question_text),
            _current_user,
            db,
        )

        # Extract result IDs depending on mode
        if response.mode == "simple":
            classified_type = (
                response.classification.answer_type if response.classification else "KB"
            )
            result_ids = [r.source_id for r in (response.results or [])]
        else:
            classified_type = "RESEARCH"
            result_ids = []
            if response.report:
                result_ids.extend(e.source_id for e in response.report.evidence)
                result_ids.extend(r.source_id for r in response.report.related_resources)

        classification_correct = classified_type == answer_type

        h1 = bool(q.target_id and q.target_id in result_ids[:1])
        h5 = bool(q.target_id and q.target_id in result_ids[:5])
        h10 = bool(q.target_id and q.target_id in result_ids[:10])

        return EvaluationStepResponse(
            done=False,
            total=total,
            index=index,
            question_id=str(q.id),
            answer_type=answer_type,
            difficulty=q.difficulty,
            classified_type=classified_type,
            classification_correct=classification_correct,
            target_id=q.target_id,
            hit_at_1=h1,
            hit_at_5=h5,
            hit_at_10=h10,
            error=False,
        )
    except Exception:
        logger.exception("Research evaluation failed for question %s", q.id)
        return EvaluationStepResponse(
            done=False,
            total=total,
            index=index,
            question_id=str(q.id),
            answer_type=answer_type,
            difficulty=q.difficulty,
            error=True,
        )


class FeedbackRequest(BaseModel):
    question_text: str
    classification: str | None = None
    result_id: str | None = None
    result_rank: int | None = None
    helpful: bool


class FeedbackResponse(BaseModel):
    id: str
    status: str


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Store feedback on a copilot search result."""
    feedback = CopilotFeedback(
        question_text=body.question_text,
        classification=body.classification,
        result_id=body.result_id,
        result_rank=body.result_rank,
        helpful=body.helpful,
        user_id=current_user.id,
    )
    db.add(feedback)
    await db.flush()
    return FeedbackResponse(id=feedback.id, status="stored")
