from fastapi import APIRouter

from api.v1 import auth, chat, users

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
