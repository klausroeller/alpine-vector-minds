from fastapi import APIRouter

from api.v1 import auth, chat, copilot, dashboard, evaluation, knowledge, learning, qa, users

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
router.include_router(learning.router, prefix="/learning", tags=["learning"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(qa.router, prefix="/qa", tags=["qa"])
router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
