from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from api.v1.auth import get_current_user
from api.v1.schemas.learning import (
    DetectGapRequest,
    DetectGapResponse,
    LearningEventResponse,
    PaginatedLearningResponse,
    ReviewRequest,
    ReviewResponse,
)
from vector_db.database import get_db
from vector_db.models.knowledge_article import ArticleStatus, KnowledgeArticle
from vector_db.models.learning_event import LearningEvent
from vector_db.models.user import User

router = APIRouter()


@router.get("/events", response_model=PaginatedLearningResponse)
async def list_learning_events(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedLearningResponse:
    query = select(LearningEvent)
    count_query = select(func.count()).select_from(LearningEvent)

    if status_filter:
        query = query.where(LearningEvent.final_status == status_filter)
        count_query = count_query.where(LearningEvent.final_status == status_filter)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(LearningEvent.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    events = result.scalars().all()

    # Fetch proposed KB article titles in bulk
    kb_ids = [e.proposed_kb_article_id for e in events if e.proposed_kb_article_id]
    kb_titles: dict[str, str] = {}
    if kb_ids:
        kb_result = await db.execute(
            select(KnowledgeArticle.id, KnowledgeArticle.title).where(
                KnowledgeArticle.id.in_(kb_ids)
            )
        )
        kb_titles = {row.id: row.title for row in kb_result}

    items = [
        LearningEventResponse(
            id=e.id,
            trigger_ticket_id=e.trigger_ticket_id,
            detected_gap=e.detected_gap,
            proposed_kb_article_id=e.proposed_kb_article_id,
            proposed_kb_title=kb_titles.get(e.proposed_kb_article_id)
            if e.proposed_kb_article_id
            else None,
            final_status=e.final_status,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]

    return PaginatedLearningResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/review/{event_id}", response_model=ReviewResponse)
async def review_learning_event(
    event_id: str,
    review: ReviewRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    # Fetch the learning event
    result = await db.execute(select(LearningEvent).where(LearningEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning event '{event_id}' not found",
        )

    # Update event status (decision validated by Pydantic Literal type)
    event.final_status = review.decision

    # Update the proposed KB article status
    kb_article_status: str | None = None
    if event.proposed_kb_article_id:
        kb_result = await db.execute(
            select(KnowledgeArticle).where(KnowledgeArticle.id == event.proposed_kb_article_id)
        )
        kb_article = kb_result.scalar_one_or_none()
        if kb_article:
            if review.decision == "Approved":
                kb_article.status = ArticleStatus.ACTIVE
                kb_article.updated_at = datetime.now(UTC)
            else:
                kb_article.status = ArticleStatus.ARCHIVED
                kb_article.updated_at = datetime.now(UTC)
            kb_article_status = kb_article.status

    await db.flush()

    return ReviewResponse(
        id=event.id,
        final_status=event.final_status,
        kb_article_status=kb_article_status,
    )


@router.post("/detect-gap", response_model=DetectGapResponse)
async def detect_gap(
    request: DetectGapRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DetectGapResponse:
    # Stub: will be wired to GapDetectionAgent + KBGenerationAgent in Phase 3
    return DetectGapResponse(
        gap_detected=False,
        learning_event_id=None,
        detected_gap="Stub: gap detection not yet implemented. Will be wired to AI agents in Phase 3.",
        proposed_article=None,
    )
