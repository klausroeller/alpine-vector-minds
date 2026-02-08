import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage
from agents.gap_detection import GapDetectionAgent
from agents.kb_generation import KBGenerationAgent
from api.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    EMBEDDING_TEXT_SEPARATOR,
    MAX_KB_TRANSCRIPT_CHARS,
    MAX_PAGE_SIZE,
)
from api.v1.auth import get_current_user
from api.v1.schemas.learning import (
    DetectGapRequest,
    DetectGapResponse,
    LearningEventResponse,
    PaginatedLearningResponse,
    ProposedArticle,
    ReviewRequest,
    ReviewResponse,
)
from vector_db.database import get_db
from vector_db.embeddings import EmbeddingService
from vector_db.models.conversation import Conversation
from vector_db.models.kb_lineage import KBLineage
from vector_db.models.knowledge_article import ArticleStatus, KnowledgeArticle
from vector_db.models.learning_event import LearningEvent
from vector_db.models.script import Script
from vector_db.models.ticket import Ticket
from vector_db.models.user import User
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_kb_id() -> str:
    """Generate a unique KB article ID for synthetically created articles."""
    short = uuid.uuid4().hex[:8].upper()
    return f"KB-SYNTH-{short}"


def _generate_learn_id() -> str:
    """Generate a unique learning event ID."""
    short = uuid.uuid4().hex[:8].upper()
    return f"LEARN-{short}"


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

                # Generate embedding so approved article becomes searchable
                if kb_article.embedding is None:
                    try:
                        embedding_service = EmbeddingService()
                        embed_text = kb_article.title + EMBEDDING_TEXT_SEPARATOR + kb_article.body
                        kb_article.embedding = await embedding_service.embed(embed_text)
                    except Exception:
                        logger.exception(
                            "Failed to generate embedding for article %s on approval",
                            kb_article.id,
                        )
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
    # Fetch ticket
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == request.ticket_id))
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{request.ticket_id}' not found",
        )

    # Fetch linked conversation
    conv_result = await db.execute(select(Conversation).where(Conversation.ticket_id == ticket.id))
    conversation = conv_result.scalar_one_or_none()

    # Fetch linked script (if any)
    script = None
    if ticket.script_id:
        script_result = await db.execute(select(Script).where(Script.id == ticket.script_id))
        script = script_result.scalar_one_or_none()

    # Run gap detection agent
    embedding_service = EmbeddingService()
    search_service = VectorSearchService(db)
    gap_agent = GapDetectionAgent(db, embedding_service, search_service)

    gap_input = json.dumps(
        {
            "ticket_description": ticket.description or "",
            "ticket_resolution": ticket.resolution or "",
            "ticket_category": ticket.category or "",
            "ticket_id": ticket.id,
        }
    )

    gap_response = await gap_agent.run([AgentMessage(role="user", content=gap_input)])
    gap_data = json.loads(gap_response.content)

    if not gap_data.get("gap_detected", False):
        return DetectGapResponse(
            gap_detected=False,
            detected_gap=gap_data.get("gap_description", "No gap detected."),
        )

    # Gap detected — generate KB article
    kb_gen_agent = KBGenerationAgent()

    gen_input_data: dict = {
        "ticket_id": ticket.id,
        "ticket_description": ticket.description or "",
        "ticket_resolution": ticket.resolution or "",
        "ticket_category": ticket.category or "",
        "ticket_module": ticket.module or "",
        "ticket_root_cause": ticket.root_cause or "",
        "suggested_title": gap_data.get("suggested_title"),
    }

    if conversation:
        transcript = conversation.transcript or ""
        if len(transcript) > MAX_KB_TRANSCRIPT_CHARS:
            transcript = transcript[:MAX_KB_TRANSCRIPT_CHARS] + "\n[... transcript truncated]"
        gen_input_data["conversation_transcript"] = transcript

    if script:
        gen_input_data["script_title"] = script.title
        gen_input_data["script_id"] = script.id

    gen_response = await kb_gen_agent.run(
        [AgentMessage(role="user", content=json.dumps(gen_input_data))]
    )
    article_data = json.loads(gen_response.content)

    # Create draft KB article
    kb_id = _generate_kb_id()
    title = article_data.get("title") or "Untitled"
    body = article_data.get("body") or ""
    embed_text = title + EMBEDDING_TEXT_SEPARATOR + body
    embedding = await embedding_service.embed(embed_text)

    kb_article = KnowledgeArticle(
        id=kb_id,
        title=title,
        body=body,
        category=article_data.get("category", ticket.category),
        module=ticket.module,
        status=ArticleStatus.DRAFT,
        source_type="SYNTH_FROM_TICKET",
        embedding=embedding,
    )
    db.add(kb_article)
    await db.flush()

    # Create lineage records
    lineage_ticket = KBLineage(
        kb_article_id=kb_id,
        source_id=ticket.id,
        relationship="CREATED_FROM",
        evidence_snippet=ticket.resolution[:200] if ticket.resolution else None,
        event_timestamp=datetime.now(UTC),
    )
    db.add(lineage_ticket)

    if conversation:
        lineage_conv = KBLineage(
            kb_article_id=kb_id,
            source_id=conversation.id,
            relationship="CREATED_FROM",
            evidence_snippet=conversation.transcript[:200] if conversation.transcript else None,
            event_timestamp=datetime.now(UTC),
        )
        db.add(lineage_conv)

    if script:
        lineage_script = KBLineage(
            kb_article_id=kb_id,
            source_id=script.id,
            relationship="REFERENCES",
            evidence_snippet=script.title,
            event_timestamp=datetime.now(UTC),
        )
        db.add(lineage_script)

    # Create learning event
    learn_id = _generate_learn_id()
    learning_event = LearningEvent(
        id=learn_id,
        trigger_ticket_id=ticket.id,
        detected_gap=gap_data.get("gap_description", ""),
        proposed_kb_article_id=kb_id,
        final_status="Pending",
    )
    db.add(learning_event)

    await db.flush()

    return DetectGapResponse(
        gap_detected=True,
        learning_event_id=learn_id,
        detected_gap=gap_data.get("gap_description", ""),
        proposed_article=ProposedArticle(
            id=kb_id,
            title=title,
            body=body,
            status=ArticleStatus.DRAFT,
        ),
    )
