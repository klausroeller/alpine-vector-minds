import re
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.constants import CONTENT_PREVIEW_LENGTH, SEARCH_RESULT_LIMIT


class VectorSearchService:
    """Semantic search over pgvector-indexed tables."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
                1 - (embedding <=> :embedding::vector) AS similarity_score
            FROM knowledge_articles
            WHERE status = :status
              AND embedding IS NOT NULL
              {category_clause}
            ORDER BY embedding <=> :embedding::vector
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
                1 - (embedding <=> :embedding::vector) AS similarity_score
            FROM scripts
            WHERE embedding IS NOT NULL
              {category_clause}
            ORDER BY embedding <=> :embedding::vector
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
        """Search tickets by embedding similarity on description + resolution.

        Tickets don't have their own embeddings, so we search via their linked
        KB articles and scripts as a proxy, then return ticket data.
        Falls back to searching KB articles and joining to tickets.
        """
        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "limit": limit,
            "preview_len": CONTENT_PREVIEW_LENGTH,
        }

        query = text("""
            SELECT
                t.id,
                t.description AS title,
                LEFT(t.resolution, :preview_len) AS content_preview,
                t.category,
                t.module,
                t.priority,
                t.root_cause,
                t.kb_article_id,
                t.script_id,
                1 - (ka.embedding <=> :embedding::vector) AS similarity_score
            FROM tickets t
            INNER JOIN knowledge_articles ka ON ka.id = t.kb_article_id
            WHERE ka.embedding IS NOT NULL
            ORDER BY ka.embedding <=> :embedding::vector
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

    async def search_all(
        self,
        query_embedding: list[float],
        answer_type: str,
        limit: int = SEARCH_RESULT_LIMIT,
    ) -> tuple[list[dict[str, Any]], float]:
        """Search the pool matching the classified answer_type.

        Returns (results, search_time_ms).
        """
        start = time.perf_counter()

        if answer_type == "SCRIPT":
            results = await self.search_scripts(query_embedding, limit)
        elif answer_type == "KB":
            results = await self.search_knowledge_articles(query_embedding, limit)
        elif answer_type == "TICKET_RESOLUTION":
            results = await self.search_tickets(query_embedding, limit)
        else:
            results = await self.search_knowledge_articles(query_embedding, limit)

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


def _extract_placeholders(script_text: str) -> list[str]:
    """Extract <PLACEHOLDER> tokens from script text."""
    return re.findall(r"<[A-Z_]+>", script_text or "")
