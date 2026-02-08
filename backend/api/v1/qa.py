"""QA scoring endpoints — score conversations and list results."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents import AgentMessage, QAScoringAgent
from api.v1.auth import get_current_user
from api.v1.schemas.qa import (
    CategoryScore,
    PaginatedQAResponse,
    QAScoreListItem,
    QAScoreResponse,
)
from vector_db.database import get_db
from vector_db.models.conversation import Conversation
from vector_db.models.ticket import Ticket
from vector_db.models.user import User

router = APIRouter()


@router.post("/score/{conversation_id}", response_model=QAScoreResponse)
async def score_conversation(
    conversation_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QAScoreResponse:
    """Run QA scoring on a conversation."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    ticket = await db.get(Ticket, conv.ticket_id)
    resolution = ticket.resolution if ticket else ""
    category = ticket.category if ticket else ""
    priority = ticket.priority if ticket else ""

    agent = QAScoringAgent()
    input_data = json.dumps(
        {
            "transcript": conv.transcript or "",
            "resolution": resolution or "",
            "category": category or "",
            "priority": priority or "",
        }
    )

    result = await agent.run([AgentMessage(role="user", content=input_data)])
    scores = json.loads(result.content)

    # Store on conversation
    now = datetime.now(UTC)
    conv.qa_score = scores.get("overall_score")
    conv.qa_scores_json = result.content
    conv.qa_red_flags = ",".join(scores.get("red_flags", []))
    conv.qa_scored_at = now
    await db.flush()

    categories = {}
    for key, val in scores.get("categories", {}).items():
        if isinstance(val, dict):
            categories[key] = CategoryScore(
                score=val.get("score", 0),
                weight=val.get("weight", 0),
                feedback=val.get("feedback", ""),
            )

    return QAScoreResponse(
        conversation_id=conversation_id,
        overall_score=scores.get("overall_score"),
        categories=categories,
        red_flags=scores.get("red_flags", []),
        summary=scores.get("summary", ""),
        scored_at=now,
    )


@router.get("/conversations", response_model=PaginatedQAResponse)
async def list_conversations(
    scored: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedQAResponse:
    """List conversations with optional scored/unscored filter."""
    base = select(Conversation)

    if scored is True:
        base = base.where(Conversation.qa_scored_at.isnot(None))
    elif scored is False:
        base = base.where(Conversation.qa_scored_at.is_(None))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows = (
        (
            await db.execute(
                base.order_by(Conversation.id).offset((page - 1) * page_size).limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    items = [
        QAScoreListItem(
            conversation_id=c.id,
            ticket_id=c.ticket_id,
            agent_name=c.agent_name,
            channel=c.channel,
            overall_score=c.qa_score,
            red_flags=[f for f in (c.qa_red_flags or "").split(",") if f],
            scored_at=c.qa_scored_at,
        )
        for c in rows
    ]

    return PaginatedQAResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/detail/{conversation_id}", response_model=QAScoreResponse)
async def get_qa_detail(
    conversation_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QAScoreResponse:
    """Get stored QA score detail for a conversation (without re-scoring)."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conv.qa_scored_at:
        raise HTTPException(status_code=404, detail="Conversation has not been scored yet")

    scores = json.loads(conv.qa_scores_json) if conv.qa_scores_json else {}
    categories = {}
    for key, val in scores.get("categories", {}).items():
        if isinstance(val, dict):
            categories[key] = CategoryScore(
                score=val.get("score", 0),
                weight=val.get("weight", 0),
                feedback=val.get("feedback", ""),
            )

    return QAScoreResponse(
        conversation_id=conversation_id,
        overall_score=conv.qa_score,
        categories=categories,
        red_flags=scores.get("red_flags", []),
        summary=scores.get("summary", ""),
        scored_at=conv.qa_scored_at,
    )


@router.get("/scores", response_model=PaginatedQAResponse)
async def list_qa_scores(
    min_score: float | None = Query(None, ge=0, le=100),
    has_red_flags: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedQAResponse:
    """List scored conversations with optional filters."""
    base = select(Conversation).where(Conversation.qa_scored_at.isnot(None))

    if min_score is not None:
        base = base.where(Conversation.qa_score >= min_score)
    if has_red_flags is True:
        base = base.where(
            Conversation.qa_red_flags.isnot(None),
            Conversation.qa_red_flags != "",
        )
    elif has_red_flags is False:
        base = base.where((Conversation.qa_red_flags.is_(None)) | (Conversation.qa_red_flags == ""))

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch page
    rows = (
        (
            await db.execute(
                base.order_by(Conversation.qa_scored_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    items = [
        QAScoreListItem(
            conversation_id=c.id,
            ticket_id=c.ticket_id,
            agent_name=c.agent_name,
            channel=c.channel,
            overall_score=c.qa_score,
            red_flags=[f for f in (c.qa_red_flags or "").split(",") if f],
            scored_at=c.qa_scored_at,
        )
        for c in rows
    ]

    return PaginatedQAResponse(items=items, total=total, page=page, page_size=page_size)
