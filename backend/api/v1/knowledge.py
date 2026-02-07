from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.constants import (
    CONTENT_PREVIEW_LENGTH,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from api.v1.auth import get_current_user
from api.v1.schemas.knowledge import (
    KBArticleDetailResponse,
    KBArticleListItem,
    LineageEntry,
    PaginatedKBResponse,
)
from vector_db.database import get_db
from vector_db.models.kb_lineage import KBLineage
from vector_db.models.knowledge_article import KnowledgeArticle
from vector_db.models.script import Script
from vector_db.models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedKBResponse)
async def list_knowledge_articles(
    search: str | None = Query(None, description="Search in title and body"),
    source_type: str | None = Query(None, description="Filter by source type"),
    category: str | None = Query(None, description="Filter by category"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedKBResponse:
    query = select(KnowledgeArticle)
    count_query = select(func.count()).select_from(KnowledgeArticle)

    # Apply filters
    if search:
        search_filter = KnowledgeArticle.title.ilike(f"%{search}%") | KnowledgeArticle.body.ilike(
            f"%{search}%"
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if source_type:
        query = query.where(KnowledgeArticle.source_type == source_type)
        count_query = count_query.where(KnowledgeArticle.source_type == source_type)

    if category:
        query = query.where(KnowledgeArticle.category == category)
        count_query = count_query.where(KnowledgeArticle.category == category)

    if status_filter:
        query = query.where(KnowledgeArticle.status == status_filter)
        count_query = count_query.where(KnowledgeArticle.status == status_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.order_by(KnowledgeArticle.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()

    items = [
        KBArticleListItem(
            id=a.id,
            title=a.title,
            source_type=a.source_type,
            status=a.status,
            category=a.category,
            module=a.module,
            created_at=a.created_at.isoformat(),
            body_preview=a.body[:CONTENT_PREVIEW_LENGTH] if a.body else "",
        )
        for a in articles
    ]

    return PaginatedKBResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{article_id}", response_model=KBArticleDetailResponse)
async def get_knowledge_article(
    article_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KBArticleDetailResponse:
    # Try knowledge_articles first; fall back to scripts table for SCRIPT-* IDs
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()

    if article:
        lineage_result = await db.execute(
            select(KBLineage).where(KBLineage.kb_article_id == article_id)
        )
        lineage_rows = lineage_result.scalars().all()
        lineage = [
            LineageEntry(
                source_id=row.source_id,
                relationship=row.relationship,
                evidence_snippet=row.evidence_snippet,
            )
            for row in lineage_rows
        ]
        return KBArticleDetailResponse(
            id=article.id,
            title=article.title,
            body=article.body,
            source_type=article.source_type,
            status=article.status,
            category=article.category,
            module=article.module,
            tags=article.tags,
            created_at=article.created_at.isoformat(),
            updated_at=article.updated_at.isoformat(),
            lineage=lineage,
        )

    # Fall back to scripts table
    if article_id.startswith("SCRIPT-"):
        script_result = await db.execute(select(Script).where(Script.id == article_id))
        script = script_result.scalar_one_or_none()
        if script:
            return KBArticleDetailResponse(
                id=script.id,
                title=script.title,
                body=script.script_text,
                source_type="script",
                status="ACTIVE",
                category=script.category,
                module=script.module,
                tags=None,
                created_at=script.created_at.isoformat(),
                updated_at=script.updated_at.isoformat(),
                lineage=[],
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge article '{article_id}' not found",
    )
