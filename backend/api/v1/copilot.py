from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import get_current_user
from api.v1.schemas.copilot import (
    Classification,
    CopilotAskRequest,
    CopilotAskResponse,
    EvaluationResponse,
)
from vector_db.database import get_db
from vector_db.models.user import User

router = APIRouter()


@router.post("/ask", response_model=CopilotAskResponse)
async def copilot_ask(
    request: CopilotAskRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopilotAskResponse:
    # Stub: will be wired to TriageAgent + VectorSearchService in Phase 3
    return CopilotAskResponse(
        classification=Classification(
            answer_type="KB",
            confidence=0.0,
            reasoning="Stub: classification not yet implemented. Will be wired to AI agents in Phase 3.",
        ),
        results=[],
        metadata={"stub": True, "message": "Copilot not yet connected to AI agents"},
    )


@router.get("/evaluate", response_model=EvaluationResponse)
async def copilot_evaluate(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    # Stub: will iterate all ground-truth questions through TriageAgent in Phase 3
    return EvaluationResponse(
        total_questions=0,
        classification_accuracy=0.0,
        retrieval_accuracy={"hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0},
        by_answer_type={},
        evaluated_at="stub",
    )
