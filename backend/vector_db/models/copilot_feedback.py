"""Model for storing copilot search result feedback."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from vector_db.database import Base


class CopilotFeedback(Base):
    __tablename__ = "copilot_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
