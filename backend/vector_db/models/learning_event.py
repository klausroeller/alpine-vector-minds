from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from vector_db.database import Base


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # LEARN-0001 from dataset
    trigger_ticket_id: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("tickets.id"), nullable=True
    )
    detected_gap: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_kb_article_id: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("knowledge_articles.id"), nullable=True
    )
    final_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
