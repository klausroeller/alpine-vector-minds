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


class DashboardMetricsResponse(BaseModel):
    knowledge_base: KnowledgeBaseMetrics
    learning: LearningMetrics
    tickets: TicketMetrics
    scripts: ScriptMetrics
