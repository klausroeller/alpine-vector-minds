"""Add QA scoring columns to conversations table (idempotent migration)."""

import asyncio

from sqlalchemy import text

from vector_db.database import engine


async def migrate() -> None:
    """Add QA scoring columns to conversations if they don't exist."""
    print("Migrating conversations table: adding QA scoring columns...")

    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS qa_score FLOAT")
        )
        await conn.execute(
            text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS qa_scores_json TEXT")
        )
        await conn.execute(
            text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS qa_red_flags TEXT")
        )
        await conn.execute(
            text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS qa_scored_at TIMESTAMPTZ")
        )
        print("  QA columns added (or already exist).")

    print("Migration complete.")
    await engine.dispose()


def main() -> None:
    asyncio.run(migrate())


if __name__ == "__main__":
    main()
