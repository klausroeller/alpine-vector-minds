"""Add embedding column to tickets table (idempotent migration)."""

import asyncio

from sqlalchemy import text

from vector_db.database import engine


async def migrate() -> None:
    """Add embedding vector column to tickets if it doesn't exist."""
    print("Migrating tickets table: adding embedding column...")

    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS embedding vector(1536)")
        )
        print("  embedding column added (or already exists).")

    print("Migration complete.")
    await engine.dispose()


def main() -> None:
    asyncio.run(migrate())


if __name__ == "__main__":
    main()
