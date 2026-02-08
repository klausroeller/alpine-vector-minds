"""Evaluation endpoints — store and retrieve evaluation run results."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import get_current_user
from vector_db.database import get_db
from vector_db.models.evaluation_run import EvaluationRun
from vector_db.models.user import User

router = APIRouter()


class EvaluationRunRequest(BaseModel):
    total_questions: int
    classification_accuracy: float
    hit_at_1: float
    hit_at_5: float
    hit_at_10: float
    by_answer_type: dict | None = None
    by_difficulty: dict | None = None
    errors: int = 0
    evaluated_at: str


class EvaluationRunResponse(BaseModel):
    id: str
    total_questions: int
    classification_accuracy: float
    hit_at_1: float
    hit_at_5: float
    hit_at_10: float
    by_answer_type: dict | None = None
    by_difficulty: dict | None = None
    errors: int
    evaluated_at: str


@router.post("/results", response_model=EvaluationRunResponse)
async def store_evaluation_results(
    body: EvaluationRunRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationRunResponse:
    """Store an evaluation run from the CLI script."""
    run = EvaluationRun(
        total_questions=body.total_questions,
        classification_accuracy=body.classification_accuracy,
        hit_at_1=body.hit_at_1,
        hit_at_5=body.hit_at_5,
        hit_at_10=body.hit_at_10,
        by_answer_type_json=json.dumps(body.by_answer_type) if body.by_answer_type else None,
        by_difficulty_json=json.dumps(body.by_difficulty) if body.by_difficulty else None,
        errors=body.errors,
        evaluated_at=datetime.fromisoformat(body.evaluated_at),
    )
    db.add(run)
    await db.flush()

    return EvaluationRunResponse(
        id=run.id,
        total_questions=run.total_questions,
        classification_accuracy=run.classification_accuracy,
        hit_at_1=run.hit_at_1,
        hit_at_5=run.hit_at_5,
        hit_at_10=run.hit_at_10,
        by_answer_type=body.by_answer_type,
        by_difficulty=body.by_difficulty,
        errors=run.errors,
        evaluated_at=body.evaluated_at,
    )


@router.get("/latest", response_model=EvaluationRunResponse | None)
async def get_latest_evaluation(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationRunResponse | None:
    """Get the most recent evaluation run."""
    run = (
        await db.execute(select(EvaluationRun).order_by(EvaluationRun.evaluated_at.desc()).limit(1))
    ).scalar_one_or_none()

    if not run:
        return None

    return EvaluationRunResponse(
        id=run.id,
        total_questions=run.total_questions,
        classification_accuracy=run.classification_accuracy,
        hit_at_1=run.hit_at_1,
        hit_at_5=run.hit_at_5,
        hit_at_10=run.hit_at_10,
        by_answer_type=json.loads(run.by_answer_type_json) if run.by_answer_type_json else None,
        by_difficulty=json.loads(run.by_difficulty_json) if run.by_difficulty_json else None,
        errors=run.errors,
        evaluated_at=run.evaluated_at.isoformat() if run.evaluated_at else "",
    )
