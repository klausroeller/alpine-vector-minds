from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "Alpine Vector Minds API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/alpine_vector_minds"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # SupportMind AI
    OPENAI_CHAT_MODEL: str = "gpt-5"
    KB_GAP_THRESHOLD: float = 0.85
    SEARCH_RESULT_LIMIT: int = 5

    # Default dev user (seeded on first DB init when both email and password are set)
    DEFAULT_USER_EMAIL: str | None = None
    DEFAULT_USER_PASSWORD: str | None = None
    DEFAULT_USER_NAME: str | None = None


settings = Settings()
