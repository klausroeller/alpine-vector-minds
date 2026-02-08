"""Generate vector embeddings for knowledge articles, scripts, and questions."""

import asyncio
from collections.abc import Callable

from sqlalchemy import select

from vector_db.database import async_session_maker, engine
from vector_db.embeddings import EmbeddingService
from vector_db.models.knowledge_article import KnowledgeArticle
from vector_db.models.question import Question
from vector_db.models.script import Script
from vector_db.models.ticket import Ticket

BATCH_SIZE = 100


async def generate_embeddings_for_table(
    service: EmbeddingService,
    model_class: type,
    text_fn: Callable[[object], str],
    label: str,
) -> None:
    """Generate embeddings for all rows in a table where embedding IS NULL."""
    async with async_session_maker() as session:
        result = await session.execute(select(model_class).where(model_class.embedding.is_(None)))
        rows = list(result.scalars().all())

        if not rows:
            print(f"  {label}: all embeddings already generated. Skipping.")
            return

        total = len(rows)
        print(f"  {label}: generating embeddings for {total} rows...")

        for i in range(0, total, BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            texts = [text_fn(row) for row in batch]
            embeddings = await service.embed_batch(texts)

            for row, emb in zip(batch, embeddings, strict=True):
                row.embedding = emb

            await session.flush()
            done = min(i + BATCH_SIZE, total)
            print(f"    {label}: {done}/{total}")

        await session.commit()
        print(f"  {label}: done.")


def kb_text(article: KnowledgeArticle) -> str:
    """Build embedding text for a knowledge article."""
    parts = [article.title]
    if article.tags:
        parts.append(f"Tags: {article.tags}")
    parts.append(article.body)
    return "\n".join(parts)


def script_text(script: Script) -> str:
    """Build embedding text for a script."""
    parts = [script.title]
    if script.purpose:
        parts.append(script.purpose)
    parts.append(script.script_text)
    return "\n".join(parts)


def ticket_text(ticket: Ticket) -> str:
    """Build embedding text for a ticket."""
    parts = []
    if ticket.description:
        parts.append(ticket.description)
    if ticket.resolution:
        parts.append(ticket.resolution)
    if ticket.root_cause:
        parts.append(f"Root cause: {ticket.root_cause}")
    return "\n".join(parts)


def question_text(question: Question) -> str:
    """Build embedding text for a question."""
    return question.question_text


async def generate_all() -> None:
    """Generate embeddings for all tables that need them."""
    service = EmbeddingService()

    print("Generating embeddings...")
    await generate_embeddings_for_table(service, KnowledgeArticle, kb_text, "Knowledge Articles")
    await generate_embeddings_for_table(service, Script, script_text, "Scripts")
    await generate_embeddings_for_table(service, Ticket, ticket_text, "Tickets")
    await generate_embeddings_for_table(service, Question, question_text, "Questions")
    print("All embeddings generated.")

    await engine.dispose()


def main() -> None:
    asyncio.run(generate_all())


if __name__ == "__main__":
    main()
