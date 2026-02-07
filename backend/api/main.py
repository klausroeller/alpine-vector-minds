from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from api.core.config import settings
from api.core.security import get_password_hash
from api.health import router as health_router
from api.v1 import router as v1_router
from vector_db.database import Base, async_session_maker, engine
from vector_db.models import User  # noqa: F401 - ensure model is registered with Base.metadata
from vector_db.models.user import UserRole


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup: create database tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default user on fresh database
    if settings.DEFAULT_USER_EMAIL and settings.DEFAULT_USER_PASSWORD:
        async with async_session_maker() as session:
            result = await session.execute(select(func.count()).select_from(User))
            user_count = result.scalar()
            if user_count == 0:
                user = User(
                    email=settings.DEFAULT_USER_EMAIL,
                    hashed_password=get_password_hash(settings.DEFAULT_USER_PASSWORD),
                    full_name=settings.DEFAULT_USER_NAME or None,
                    role=UserRole.ADMIN,
                )
                session.add(user)
                await session.commit()
                print(f"Seeded default user '{settings.DEFAULT_USER_EMAIL}'")

    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
