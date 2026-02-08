import re
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.constants import (
    CONTENT_PREVIEW_LENGTH,
    FTS_WEIGHT,
    HYBRID_SEARCH_OVERFETCH,
    RRF_K,
    SEARCH_RESULT_LIMIT,
    SEMANTIC_WEIGHT,
)


class VectorSearchService:
    """Hybrid search: semantic (pgvector) + full-text (tsvector) with RRF merging."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Semantic search methods ──────────────────────────────

    async def search_knowledge_articles(
        self,
        query_embedding: list[float],
        limit: int = SEARCH_RESULT_LIMIT,
        status_filter: str = "active",
        category_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search KB articles by cosine similarity."""
        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "status": status_filter,
            "limit": limit,
        }

        category_clause = ""
        if category_filter:
            category_clause = "AND category = :category"
            params["category"] = category_filter

        query = text(f"""
            SELECT
                id,
                title,
                LEFT(body, :preview_len) AS content_preview,
                category,
                source_type,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity_score
            FROM knowledge_articles
            WHERE status = :status
              AND embedding IS NOT NULL
              {category_clause}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        params["preview_len"] = CONTENT_PREVIEW_LENGTH

        result = await self.db.execute(query, params)
        rows = result.mappings().all()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content_preview": row["content_preview"],
                "category": row["category"],
                "source_type": row["source_type"],
                "similarity_score": float(row["similarity_score"]),
            }
            for row in rows
        ]

    async def search_scripts(
        self,
        query_embedding: list[float],
        limit: int = SEARCH_RESULT_LIMIT,
        category_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search scripts by cosine similarity."""
        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "limit": limit,
            "preview_len": CONTENT_PREVIEW_LENGTH,
        }

        category_clause = ""
        if category_filter:
            category_clause = "AND category = :category"
            params["category"] = category_filter

        query = text(f"""
            SELECT
                id,
                title,
                LEFT(script_text, :preview_len) AS content_preview,
                category,
                module,
                script_text,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity_score
            FROM scripts
            WHERE embedding IS NOT NULL
              {category_clause}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)

        result = await self.db.execute(query, params)
        rows = result.mappings().all()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content_preview": row["content_preview"],
                "category": row["category"],
                "module": row["module"],
                "similarity_score": float(row["similarity_score"]),
                "placeholders": _extract_placeholders(row["script_text"]),
            }
            for row in rows
        ]

    async def search_tickets(
        self,
        query_embedding: list[float],
        limit: int = SEARCH_RESULT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search tickets by cosine similarity on their own embeddings."""
        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "limit": limit,
            "preview_len": CONTENT_PREVIEW_LENGTH,
        }

        query = text("""
            SELECT
                id,
                description AS title,
                LEFT(resolution, :preview_len) AS content_preview,
                category,
                module,
                priority,
                root_cause,
                kb_article_id,
                script_id,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity_score
            FROM tickets
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)

        result = await self.db.execute(query, params)
        rows = result.mappings().all()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content_preview": row["content_preview"],
                "category": row["category"],
                "module": row["module"],
                "priority": row["priority"],
                "root_cause": row["root_cause"],
                "similarity_score": float(row["similarity_score"]),
            }
            for row in rows
        ]

    # ── Full-text search methods ─────────────────────────────

    async def fulltext_search_knowledge_articles(
        self,
        query: str,
        limit: int = SEARCH_RESULT_LIMIT,
        status_filter: str = "active",
    ) -> list[dict[str, Any]]:
        """Search KB articles via PostgreSQL full-text search."""
        params: dict[str, Any] = {
            "query": query,
            "status": status_filter,
            "limit": limit,
            "preview_len": CONTENT_PREVIEW_LENGTH,
        }

        sql = text("""
            SELECT
                id,
                title,
                LEFT(body, :preview_len) AS content_preview,
                category,
                source_type,
                ts_rank(search_vector, plainto_tsquery('english', :query)) AS fts_score
            FROM knowledge_articles
            WHERE status = :status
              AND search_vector @@ plainto_tsquery('english', :query)
            ORDER BY fts_score DESC
            LIMIT :limit
        """)

        result = await self.db.execute(sql, params)
        rows = result.mappings().all()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content_preview": row["content_preview"],
                "category": row["category"],
                "source_type": row["source_type"],
                "similarity_score": float(row["fts_score"]),
            }
            for row in rows
        ]

    async def fulltext_search_scripts(
        self,
        query: str,
        limit: int = SEARCH_RESULT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search scripts via PostgreSQL full-text search."""
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "preview_len": CONTENT_PREVIEW_LENGTH,
        }

        sql = text("""
            SELECT
                id,
                title,
                LEFT(script_text, :preview_len) AS content_preview,
                category,
                module,
                script_text,
                ts_rank(search_vector, plainto_tsquery('english', :query)) AS fts_score
            FROM scripts
            WHERE search_vector @@ plainto_tsquery('english', :query)
            ORDER BY fts_score DESC
            LIMIT :limit
        """)

        result = await self.db.execute(sql, params)
        rows = result.mappings().all()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content_preview": row["content_preview"],
                "category": row["category"],
                "module": row["module"],
                "similarity_score": float(row["fts_score"]),
                "placeholders": _extract_placeholders(row["script_text"]),
            }
            for row in rows
        ]

    async def fulltext_search_tickets(
        self,
        query: str,
        limit: int = SEARCH_RESULT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search tickets via PostgreSQL full-text search."""
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "preview_len": CONTENT_PREVIEW_LENGTH,
        }

        sql = text("""
            SELECT
                id,
                description AS title,
                LEFT(resolution, :preview_len) AS content_preview,
                category,
                module,
                priority,
                root_cause,
                kb_article_id,
                script_id,
                ts_rank(search_vector, plainto_tsquery('english', :query)) AS fts_score
            FROM tickets
            WHERE search_vector @@ plainto_tsquery('english', :query)
            ORDER BY fts_score DESC
            LIMIT :limit
        """)

        result = await self.db.execute(sql, params)
        rows = result.mappings().all()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content_preview": row["content_preview"],
                "category": row["category"],
                "module": row["module"],
                "priority": row["priority"],
                "root_cause": row["root_cause"],
                "similarity_score": float(row["fts_score"]),
            }
            for row in rows
        ]

    # ── Hybrid search (semantic + FTS + RRF) ─────────────────

    async def search_all(
        self,
        query_embedding: list[float],
        answer_type: str,
        limit: int = SEARCH_RESULT_LIMIT,
        raw_question: str | None = None,
    ) -> tuple[list[dict[str, Any]], float]:
        """Hybrid search: semantic + full-text merged via Reciprocal Rank Fusion.

        Uses query_embedding for semantic search and raw_question for FTS.
        Returns (results, search_time_ms).
        """
        start = time.perf_counter()
        overfetch = HYBRID_SEARCH_OVERFETCH

        if answer_type == "SCRIPT":
            semantic = await self.search_scripts(query_embedding, overfetch)
            fts = (
                await self.fulltext_search_scripts(raw_question, overfetch) if raw_question else []
            )
        elif answer_type == "KB":
            semantic = await self.search_knowledge_articles(query_embedding, overfetch)
            fts = (
                await self.fulltext_search_knowledge_articles(raw_question, overfetch)
                if raw_question
                else []
            )
        elif answer_type == "TICKET_RESOLUTION":
            semantic = await self.search_tickets(query_embedding, overfetch)
            fts = (
                await self.fulltext_search_tickets(raw_question, overfetch) if raw_question else []
            )
        else:
            semantic = await self.search_knowledge_articles(query_embedding, overfetch)
            fts = (
                await self.fulltext_search_knowledge_articles(raw_question, overfetch)
                if raw_question
                else []
            )

        results = reciprocal_rank_fusion(semantic, fts)[:limit]

        elapsed_ms = (time.perf_counter() - start) * 1000
        return results, elapsed_ms

    async def find_best_kb_match(
        self,
        query_embedding: list[float],
    ) -> dict[str, Any] | None:
        """Find the single best matching KB article. Used for gap detection."""
        results = await self.search_knowledge_articles(
            query_embedding, limit=1, status_filter="active"
        )
        return results[0] if results else None


def reciprocal_rank_fusion(
    semantic_results: list[dict[str, Any]],
    fts_results: list[dict[str, Any]],
    k: int = RRF_K,
    semantic_weight: float = SEMANTIC_WEIGHT,
    fts_weight: float = FTS_WEIGHT,
) -> list[dict[str, Any]]:
    """Merge two ranked result lists using weighted Reciprocal Rank Fusion.

    RRF score = weight / (k + rank), summed across lists for matching IDs.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict[str, Any]] = {}

    for rank, item in enumerate(semantic_results, start=1):
        doc_id = item["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + semantic_weight / (k + rank)
        items[doc_id] = item

    for rank, item in enumerate(fts_results, start=1):
        doc_id = item["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + fts_weight / (k + rank)
        if doc_id not in items:
            items[doc_id] = item

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [
        {**items[doc_id], "similarity_score": round(scores[doc_id], 6)} for doc_id in sorted_ids
    ]


def _extract_placeholders(script_text: str) -> list[str]:
    """Extract <PLACEHOLDER> tokens from script text."""
    return re.findall(r"<[A-Z_]+>", script_text or "")
