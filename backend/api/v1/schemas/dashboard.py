from pydantic import BaseModel


class CategoryCount(BaseModel):
    name: str
    count: int


class KnowledgeBaseMetrics(BaseModel):
    total_articles: int
    by_source_type: dict[str, int]
    by_status: dict[str, int]
    articles_with_embeddings: int
    categories: list[CategoryCount]


class LearningMetrics(BaseModel):
    total_events: int
    by_status: dict[str, int]
    approval_rate: float


class TicketMetrics(BaseModel):
    total: int
    by_priority: dict[str, int]
    by_root_cause: list[CategoryCount]


class ScriptMetrics(BaseModel):
    total: int
    by_category: list[CategoryCount]


class QAMonthlyScore(BaseModel):
    month: str  # "YYYY-MM"
    avg_score: float
    count: int


class QAMetrics(BaseModel):
    total_scored: int
    average_score: float
    red_flag_count: int
    monthly_scores: list[QAMonthlyScore] = []


class DifficultyMetrics(BaseModel):
    count: int
    classification_correct: float
    hit_at_1: float
    hit_at_5: float


class EvaluationMetrics(BaseModel):
    classification_accuracy: float
    hit_at_1: float
    hit_at_5: float
    hit_at_10: float
    total_questions: int
    evaluated_at: str
    by_difficulty: dict[str, DifficultyMetrics] | None = None


class FeedbackMetrics(BaseModel):
    total_feedback: int
    helpful_count: int
    helpful_rate: float


class DashboardMetricsResponse(BaseModel):
    knowledge_base: KnowledgeBaseMetrics
    learning: LearningMetrics
    tickets: TicketMetrics
    scripts: ScriptMetrics
    qa: QAMetrics | None = None
    evaluation: EvaluationMetrics | None = None
    feedback: FeedbackMetrics | None = None
