from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import get_current_user
from api.v1.schemas.dashboard import (
    CategoryCount,
    DashboardMetricsResponse,
    KnowledgeBaseMetrics,
    LearningMetrics,
    ScriptMetrics,
    TicketMetrics,
)
from vector_db.database import get_db
from vector_db.models.knowledge_article import KnowledgeArticle
from vector_db.models.learning_event import LearningEvent
from vector_db.models.script import Script
from vector_db.models.ticket import Ticket
from vector_db.models.user import User

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardMetricsResponse:
    # --- Knowledge Base Metrics ---
    kb_total = (await db.execute(select(func.count()).select_from(KnowledgeArticle))).scalar() or 0

    # By source type
    kb_source_rows = await db.execute(
        select(KnowledgeArticle.source_type, func.count()).group_by(KnowledgeArticle.source_type)
    )
    kb_by_source = {row[0] or "unknown": row[1] for row in kb_source_rows}

    # By status
    kb_status_rows = await db.execute(
        select(KnowledgeArticle.status, func.count()).group_by(KnowledgeArticle.status)
    )
    kb_by_status = {row[0]: row[1] for row in kb_status_rows}

    # Articles with embeddings
    kb_with_embeddings = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeArticle)
            .where(KnowledgeArticle.embedding.isnot(None))
        )
    ).scalar() or 0

    # KB categories
    kb_cat_rows = await db.execute(
        select(KnowledgeArticle.category, func.count())
        .where(KnowledgeArticle.category.isnot(None))
        .group_by(KnowledgeArticle.category)
        .order_by(func.count().desc())
        .limit(20)
    )
    kb_categories = [CategoryCount(name=row[0], count=row[1]) for row in kb_cat_rows]

    # --- Learning Metrics ---
    learn_total = (await db.execute(select(func.count()).select_from(LearningEvent))).scalar() or 0

    learn_status_rows = await db.execute(
        select(LearningEvent.final_status, func.count()).group_by(LearningEvent.final_status)
    )
    learn_by_status = {row[0] or "unknown": row[1] for row in learn_status_rows}

    approved_count = learn_by_status.get("Approved", 0)
    decided_count = approved_count + learn_by_status.get("Rejected", 0)
    approval_rate = round(approved_count / decided_count, 2) if decided_count > 0 else 0.0

    # --- Ticket Metrics ---
    ticket_total = (await db.execute(select(func.count()).select_from(Ticket))).scalar() or 0

    ticket_priority_rows = await db.execute(
        select(Ticket.priority, func.count()).group_by(Ticket.priority)
    )
    ticket_by_priority = {row[0]: row[1] for row in ticket_priority_rows}

    ticket_rc_rows = await db.execute(
        select(Ticket.root_cause, func.count())
        .where(Ticket.root_cause.isnot(None))
        .group_by(Ticket.root_cause)
        .order_by(func.count().desc())
    )
    ticket_by_root_cause = [CategoryCount(name=row[0], count=row[1]) for row in ticket_rc_rows]

    # --- Script Metrics ---
    script_total = (await db.execute(select(func.count()).select_from(Script))).scalar() or 0

    script_cat_rows = await db.execute(
        select(Script.category, func.count())
        .where(Script.category.isnot(None))
        .group_by(Script.category)
        .order_by(func.count().desc())
    )
    script_by_category = [CategoryCount(name=row[0], count=row[1]) for row in script_cat_rows]

    return DashboardMetricsResponse(
        knowledge_base=KnowledgeBaseMetrics(
            total_articles=kb_total,
            by_source_type=kb_by_source,
            by_status=kb_by_status,
            articles_with_embeddings=kb_with_embeddings,
            categories=kb_categories,
        ),
        learning=LearningMetrics(
            total_events=learn_total,
            by_status=learn_by_status,
            approval_rate=approval_rate,
        ),
        tickets=TicketMetrics(
            total=ticket_total,
            by_priority=ticket_by_priority,
            by_root_cause=ticket_by_root_cause,
        ),
        scripts=ScriptMetrics(
            total=script_total,
            by_category=script_by_category,
        ),
    )
