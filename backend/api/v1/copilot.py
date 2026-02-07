import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage
from agents.triage import TriageAgent
from api.v1.auth import get_current_user
from api.v1.schemas.copilot import (
    ByAnswerTypeStats,
    Classification,
    CopilotAskRequest,
    CopilotAskResponse,
    EvaluationResponse,
    ProvenanceInfo,
    RetrievalAccuracy,
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


async def _get_provenance(db: AsyncSession, article_id: str) -> ProvenanceInfo | None:
    """Fetch provenance info from kb_lineage for a KB article."""
    result = await db.execute(
        select(KBLineage).where(KBLineage.kb_article_id == article_id)
    )
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
        elif row.relationship == "REFERENCES" and row.source_id and row.source_id.startswith("SCRIPT-"):
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

    response = await triage_agent.run(
        [AgentMessage(role="user", content=request.question)]
    )

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
        source_type = r.get("source_type", "")
        source_id = r.get("id", "")

        # Enrich with provenance for KB articles with synthetic source types
        provenance = None
        if source_type == "KB" and r.get("source_type_detail", r.get("source_type", "")):
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


@router.get("/evaluate", response_model=EvaluationResponse)
async def copilot_evaluate(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    # Fetch all ground-truth questions
    result = await db.execute(select(Question))
    questions = result.scalars().all()

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ground-truth questions found in database",
        )

    embedding_service = EmbeddingService()
    search_service = VectorSearchService(db)
    triage_agent = TriageAgent(db, embedding_service, search_service)

    total = len(questions)
    correct_classifications = 0
    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0

    # Per answer_type tracking
    type_stats: dict[str, dict] = {}

    for q in questions:
        answer_type = q.answer_type or "UNKNOWN"

        if answer_type not in type_stats:
            type_stats[answer_type] = {
                "count": 0,
                "hit_at_1": 0,
                "hit_at_3": 0,
            }
        type_stats[answer_type]["count"] += 1

        try:
            response = await triage_agent.run(
                [AgentMessage(role="user", content=q.question_text)]
            )
            payload = json.loads(response.content)
            classified_type = payload["classification"]["answer_type"]
            result_ids = [r.get("id", "") for r in payload.get("results", [])]

            # Classification accuracy
            if classified_type == answer_type:
                correct_classifications += 1

            # Retrieval accuracy — check if target_id appears in top-k
            if q.target_id:
                if q.target_id in result_ids[:1]:
                    hit_at_1 += 1
                    hit_at_3 += 1
                    hit_at_5 += 1
                    type_stats[answer_type]["hit_at_1"] += 1
                    type_stats[answer_type]["hit_at_3"] += 1
                elif q.target_id in result_ids[:3]:
                    hit_at_3 += 1
                    hit_at_5 += 1
                    type_stats[answer_type]["hit_at_3"] += 1
                elif q.target_id in result_ids[:5]:
                    hit_at_5 += 1

        except Exception:
            logger.exception("Evaluation failed for question %s", q.id)

    by_answer_type = {}
    for at, stats in type_stats.items():
        count = stats["count"]
        by_answer_type[at] = ByAnswerTypeStats(
            count=count,
            hit_at_1=stats["hit_at_1"] / count if count > 0 else 0.0,
            hit_at_3=stats["hit_at_3"] / count if count > 0 else 0.0,
        )

    questions_with_targets = sum(1 for q in questions if q.target_id)

    return EvaluationResponse(
        total_questions=total,
        classification_accuracy=correct_classifications / total if total > 0 else 0.0,
        retrieval_accuracy=RetrievalAccuracy(
            hit_at_1=hit_at_1 / questions_with_targets if questions_with_targets > 0 else 0.0,
            hit_at_3=hit_at_3 / questions_with_targets if questions_with_targets > 0 else 0.0,
            hit_at_5=hit_at_5 / questions_with_targets if questions_with_targets > 0 else 0.0,
        ),
        by_answer_type=by_answer_type,
        evaluated_at=datetime.now(UTC).isoformat(),
    )
