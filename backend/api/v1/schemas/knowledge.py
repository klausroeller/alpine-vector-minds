from pydantic import BaseModel


class KBArticleListItem(BaseModel):
    id: str
    title: str
    source_type: str | None
    status: str
    category: str | None
    module: str | None
    created_at: str
    body_preview: str

    model_config = {"from_attributes": True}


class LineageEntry(BaseModel):
    source_id: str | None
    relationship: str | None
    evidence_snippet: str | None


class KBArticleDetailResponse(BaseModel):
    id: str
    title: str
    body: str
    source_type: str | None
    status: str
    category: str | None
    module: str | None
    tags: str | None
    created_at: str
    updated_at: str
    lineage: list[LineageEntry]

    model_config = {"from_attributes": True}


class PaginatedKBResponse(BaseModel):
    items: list[KBArticleListItem]
    total: int
    page: int
    page_size: int
