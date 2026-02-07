from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.health import router as health_router
from api.v1 import router as v1_router
from vector_db.database import Base, engine
from vector_db.models import User  # noqa: F401 - ensure model is registered with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup: create database tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
