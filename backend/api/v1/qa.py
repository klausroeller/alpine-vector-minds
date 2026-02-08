"""QA scoring endpoints — score conversations and list results."""

import asyncio
import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents import AgentMessage, QAScoringAgent
from agents.qa_scoring import extract_red_flags, parse_score_pct
from api.v1.auth import get_current_user
from api.v1.schemas.qa import (
    PaginatedQAResponse,
    QADetailResponse,
    QAScoreListItem,
    ScoreAllResponse,
)
from vector_db.database import get_db
from vector_db.models.conversation import Conversation
from vector_db.models.ticket import Ticket
from vector_db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

SCORE_ALL_CONCURRENCY = 5


async def _score_single(
    conv: Conversation,
    ticket: Ticket | None,
    agent: QAScoringAgent,
) -> dict | None:
    """Run QA scoring on a single conversation. Returns parsed scores or None on error."""
    try:
        input_data = json.dumps(
            {
                "transcript": conv.transcript or "",
                "resolution": ticket.resolution if ticket else "",
                "description": ticket.description if ticket else "",
                "category": ticket.category if ticket else "",
                "priority": ticket.priority if ticket else "",
                "module": ticket.module if ticket else "",
                "product": ticket.product if ticket else "",
                "root_cause": ticket.root_cause if ticket else "",
                "kb_article_id": ticket.kb_article_id if ticket else "",
                "script_id": ticket.script_id if ticket else "",
            }
        )
        result = await agent.run([AgentMessage(role="user", content=input_data)])
        return json.loads(result.content)
    except Exception:
        logger.exception("QA scoring failed for %s", conv.id)
        return None


def _store_scores(conv: Conversation, scores: dict) -> None:
    """Store QA scores on a conversation record."""
    overall = parse_score_pct(scores.get("Overall_Weighted_Score"))
    red_flags = extract_red_flags(scores)

    conv.qa_score = overall
    conv.qa_scores_json = json.dumps(scores)
    conv.qa_red_flags = ",".join(red_flags)
    conv.qa_scored_at = datetime.now(UTC)


@router.post("/score/{conversation_id}", response_model=QADetailResponse)
async def score_conversation(
    conversation_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QADetailResponse:
    """Run QA scoring on a conversation."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    ticket = await db.get(Ticket, conv.ticket_id)
    agent = QAScoringAgent()
    scores = await _score_single(conv, ticket, agent)

    if scores is None:
        raise HTTPException(status_code=500, detail="QA scoring failed")

    _store_scores(conv, scores)
    await db.flush()

    red_flags = extract_red_flags(scores)

    return QADetailResponse(
        conversation_id=conversation_id,
        overall_score=conv.qa_score,
        scores_json=scores,
        red_flags=red_flags,
        transcript=conv.transcript,
        scored_at=conv.qa_scored_at,
    )


@router.post("/score-all", response_model=ScoreAllResponse)
async def score_all_conversations(
    limit: int = Query(50, ge=1, le=200),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoreAllResponse:
    """Score all unscored conversations (up to limit)."""
    # Get unscored conversations
    unscored_q = (
        select(Conversation)
        .where(Conversation.qa_scored_at.is_(None))
        .order_by(Conversation.id)
        .limit(limit)
    )
    unscored = (await db.execute(unscored_q)).scalars().all()

    if not unscored:
        # Check remaining
        remaining_count = (
            await db.execute(
                select(func.count()).select_from(
                    select(Conversation)
                    .where(Conversation.qa_scored_at.is_(None))
                    .subquery()
                )
            )
        ).scalar() or 0
        return ScoreAllResponse(scored=0, errors=0, remaining=remaining_count)

    # Pre-fetch all tickets
    ticket_ids = {c.ticket_id for c in unscored}
    tickets_q = select(Ticket).where(Ticket.id.in_(ticket_ids))
    tickets_map = {
        t.id: t for t in (await db.execute(tickets_q)).scalars().all()
    }

    # Score concurrently with semaphore
    agent = QAScoringAgent()
    semaphore = asyncio.Semaphore(SCORE_ALL_CONCURRENCY)

    async def _limited_score(conv: Conversation) -> tuple[Conversation, dict | None]:
        async with semaphore:
            ticket = tickets_map.get(conv.ticket_id)
            scores = await _score_single(conv, ticket, agent)
            return conv, scores

    tasks = [_limited_score(c) for c in unscored]
    results = await asyncio.gather(*tasks)

    scored = 0
    errors = 0
    for conv, scores in results:
        if scores is not None:
            _store_scores(conv, scores)
            scored += 1
        else:
            errors += 1

    await db.flush()

    # Count remaining unscored
    remaining_count = (
        await db.execute(
            select(func.count()).select_from(
                select(Conversation)
                .where(Conversation.qa_scored_at.is_(None))
                .subquery()
            )
        )
    ).scalar() or 0

    return ScoreAllResponse(scored=scored, errors=errors, remaining=remaining_count)


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


@router.get("/detail/{conversation_id}", response_model=QADetailResponse)
async def get_qa_detail(
    conversation_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QADetailResponse:
    """Get stored QA score detail for a conversation (without re-scoring)."""
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conv.qa_scored_at:
        raise HTTPException(status_code=404, detail="Conversation has not been scored yet")

    scores = json.loads(conv.qa_scores_json) if conv.qa_scores_json else {}
    red_flags = extract_red_flags(scores) if scores else []

    return QADetailResponse(
        conversation_id=conversation_id,
        overall_score=conv.qa_score,
        scores_json=scores,
        red_flags=red_flags,
        transcript=conv.transcript,
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
