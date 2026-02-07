"""Create IVFFlat vector indexes for embedding columns."""

import asyncio

from sqlalchemy import text

from vector_db.database import engine

INDEXES = [
    {
        "name": "ix_knowledge_articles_embedding",
        "table": "knowledge_articles",
        "column": "embedding",
        "lists": 50,
    },
    {
        "name": "ix_scripts_embedding",
        "table": "scripts",
        "column": "embedding",
        "lists": 20,
    },
    {
        "name": "ix_questions_embedding",
        "table": "questions",
        "column": "embedding",
        "lists": 30,
    },
]


async def create_indexes() -> None:
    """Create IVFFlat indexes on embedding columns."""
    print("Creating vector indexes...")

    async with engine.begin() as conn:
        for idx in INDEXES:
            sql = (
                f"CREATE INDEX IF NOT EXISTS {idx['name']} "
                f"ON {idx['table']} USING ivfflat ({idx['column']} vector_cosine_ops) "
                f"WITH (lists = {idx['lists']})"
            )
            await conn.execute(text(sql))
            print(f"  {idx['name']} on {idx['table']}.{idx['column']} (lists={idx['lists']})")

    print("Vector indexes created.")
    await engine.dispose()


def main() -> None:
    asyncio.run(create_indexes())


if __name__ == "__main__":
    main()
