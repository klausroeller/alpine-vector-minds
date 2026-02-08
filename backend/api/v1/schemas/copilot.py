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
    hit_at_5: float


class RetrievalAccuracy(BaseModel):
    hit_at_1: float
    hit_at_5: float
    hit_at_10: float


class EvaluationStepResponse(BaseModel):
    done: bool
    total: int
    index: int | None = None
    question_id: str | None = None
    answer_type: str | None = None
    difficulty: str | None = None
    classified_type: str | None = None
    classification_correct: bool | None = None
    target_id: str | None = None
    hit_at_1: bool | None = None
    hit_at_5: bool | None = None
    hit_at_10: bool | None = None
    error: bool = False


# --- Deep Research ---


class CopilotResearchRequest(BaseModel):
    question: str


class SubQueryInfo(BaseModel):
    query: str
    pool: str
    aspect: str


class EvidenceItem(BaseModel):
    source_id: str
    source_type: str
    title: str
    relevance: str
    content_preview: str


class RelatedResource(BaseModel):
    source_id: str
    source_type: str
    title: str
    why_relevant: str


class ResearchReport(BaseModel):
    summary: str
    evidence: list[EvidenceItem]
    related_resources: list[RelatedResource]


class CopilotResearchResponse(BaseModel):
    mode: str  # "simple" | "research"
    classification: Classification | None = None
    results: list[SearchResult] | None = None
    report: ResearchReport | None = None
    sub_queries: list[SubQueryInfo] | None = None
    metadata: dict[str, Any]


# --- Evaluation ---


class EvaluationResponse(BaseModel):
    total_questions: int
    classification_accuracy: float
    retrieval_accuracy: RetrievalAccuracy
    by_answer_type: dict[str, ByAnswerTypeStats]
    evaluated_at: str
