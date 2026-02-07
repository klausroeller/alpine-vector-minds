from typing import Any

from pydantic import BaseModel


class CopilotAskRequest(BaseModel):
    question: str


class Classification(BaseModel):
    answer_type: str  # SCRIPT | KB | TICKET_RESOLUTION
    confidence: float
    reasoning: str


class ProvenanceInfo(BaseModel):
    created_from_ticket: str | None = None
    created_from_conversation: str | None = None
    references_script: str | None = None


class SearchResult(BaseModel):
    rank: int
    source_type: str
    source_id: str
    title: str
    content_preview: str
    similarity_score: float
    category: str | None = None
    placeholders: list[str] | None = None
    provenance: ProvenanceInfo | None = None


class CopilotAskResponse(BaseModel):
    classification: Classification
    results: list[SearchResult]
    metadata: dict[str, Any]


class ByAnswerTypeStats(BaseModel):
    count: int
    hit_at_1: float
    hit_at_3: float


class RetrievalAccuracy(BaseModel):
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float


class EvaluationResponse(BaseModel):
    total_questions: int
    classification_accuracy: float
    retrieval_accuracy: RetrievalAccuracy
    by_answer_type: dict[str, ByAnswerTypeStats]
    evaluated_at: str
