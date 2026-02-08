from datetime import datetime

from pydantic import BaseModel


class CategoryScore(BaseModel):
    score: float
    weight: float
    feedback: str


class QAScoreResponse(BaseModel):
    conversation_id: str
    overall_score: float | None
    categories: dict[str, CategoryScore]
    red_flags: list[str]
    summary: str
    scored_at: datetime | None


class QAScoreListItem(BaseModel):
    conversation_id: str
    ticket_id: str
    agent_name: str | None
    channel: str | None
    overall_score: float | None
    red_flags: list[str]
    scored_at: datetime | None


class PaginatedQAResponse(BaseModel):
    items: list[QAScoreListItem]
    total: int
    page: int
    page_size: int
