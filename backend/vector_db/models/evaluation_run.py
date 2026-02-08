"""Model for storing copilot evaluation run results."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from vector_db.database import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    classification_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    hit_at_1: Mapped[float] = mapped_column(Float, nullable=False)
    hit_at_5: Mapped[float] = mapped_column(Float, nullable=False)
    hit_at_10: Mapped[float] = mapped_column(Float, nullable=False)
    by_answer_type_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    by_difficulty_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
