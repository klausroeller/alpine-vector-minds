"""Create full-text search (tsvector) columns and GIN indexes."""

import asyncio

from sqlalchemy import text

from vector_db.database import engine

FULLTEXT_CONFIGS = [
    {
        "table": "knowledge_articles",
        "column": "search_vector",
        "expression": (
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(body, '')), 'B')"
        ),
        "index_name": "ix_knowledge_articles_fts",
    },
    {
        "table": "scripts",
        "column": "search_vector",
        "expression": (
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(purpose, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(script_text, '')), 'B')"
        ),
        "index_name": "ix_scripts_fts",
    },
    {
        "table": "tickets",
        "column": "search_vector",
        "expression": (
            "setweight(to_tsvector('english', coalesce(description, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(resolution, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(root_cause, '')), 'B')"
        ),
        "index_name": "ix_tickets_fts",
    },
]


async def create_fulltext_indexes() -> None:
    """Add tsvector columns and GIN indexes for full-text search."""
    print("Creating full-text search columns and indexes...")

    async with engine.begin() as conn:
        for cfg in FULLTEXT_CONFIGS:
            table = cfg["table"]
            col = cfg["column"]
            expr = cfg["expression"]
            idx = cfg["index_name"]

            # Add generated tsvector column (idempotent via IF NOT EXISTS check)
            await conn.execute(
                text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{table}' AND column_name = '{col}'
                    ) THEN
                        ALTER TABLE {table}
                        ADD COLUMN {col} tsvector
                        GENERATED ALWAYS AS ({expr}) STORED;
                    END IF;
                END $$;
            """)
            )
            print(f"  {table}.{col} column ensured.")

            # Create GIN index
            await conn.execute(
                text(f"CREATE INDEX IF NOT EXISTS {idx} ON {table} USING gin ({col})")
            )
            print(f"  {idx} index created.")

    print("Full-text search setup complete.")
    await engine.dispose()


def main() -> None:
    asyncio.run(create_fulltext_indexes())


if __name__ == "__main__":
    main()
