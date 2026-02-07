from typing import Literal

from pydantic import BaseModel


class LearningEventResponse(BaseModel):
    id: str
    trigger_ticket_id: str | None
    detected_gap: str | None
    proposed_kb_article_id: str | None
    proposed_kb_title: str | None
    final_status: str | None
    created_at: str

    model_config = {"from_attributes": True}


class PaginatedLearningResponse(BaseModel):
    items: list[LearningEventResponse]
    total: int
    page: int
    page_size: int


class ReviewRequest(BaseModel):
    decision: Literal["Approved", "Rejected"]


class ReviewResponse(BaseModel):
    id: str
    final_status: str
    kb_article_status: str | None


class DetectGapRequest(BaseModel):
    ticket_id: str


class ProposedArticle(BaseModel):
    id: str
    title: str
    body: str
    status: str


class DetectGapResponse(BaseModel):
    gap_detected: bool
    learning_event_id: str | None = None
    detected_gap: str | None = None
    proposed_article: ProposedArticle | None = None
