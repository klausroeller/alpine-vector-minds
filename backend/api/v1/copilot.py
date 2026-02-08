import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage
from agents.triage import TriageAgent
from api.v1.auth import get_current_user
from api.v1.schemas.copilot import (
    Classification,
    CopilotAskRequest,
    CopilotAskResponse,
    EvaluationStepResponse,
    ProvenanceInfo,
    SearchResult,
)
from vector_db.database import get_db
from vector_db.embeddings import EmbeddingService
from vector_db.models.kb_lineage import KBLineage
from vector_db.models.question import Question
from vector_db.models.user import User
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

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

    results: list[SearchResult] = []
    for r in raw_results:
        raw_type = r.get("source_type", "")
        source_type = _SOURCE_TYPE_MAP.get(raw_type, raw_type)
        source_id = r.get("id", "")

        # Enrich with provenance for KB articles
        provenance = None
        if source_type == "kb_article":
            provenance = await _get_provenance(db, source_id)

        results.append(
            SearchResult(
                rank=r["rank"],
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

    return CopilotAskResponse(
        classification=classification,
        results=results,
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
        embedding_service = EmbeddingService()
        search_service = VectorSearchService(db)
        triage_agent = TriageAgent(db, embedding_service, search_service)

        response = await triage_agent.run([AgentMessage(role="user", content=q.question_text)])
        payload = json.loads(response.content)
        classified_type = payload["classification"]["answer_type"]
        result_ids = [r.get("id", "") for r in payload.get("results", [])]

        classification_correct = classified_type == answer_type

        h1 = bool(q.target_id and q.target_id in result_ids[:1])
        h3 = bool(q.target_id and q.target_id in result_ids[:3])
        h5 = bool(q.target_id and q.target_id in result_ids[:5])

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
            hit_at_3=h3,
            hit_at_5=h5,
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
