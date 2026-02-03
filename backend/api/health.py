from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Alpine Vector Minds API"}
