from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "EHS Inspection API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"

    # ── CORS ─────────────────────────────────────────────────────
    # Comma-separated in .env: ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ── Rate limiting ─────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "200/minute"
    RATE_LIMIT_HEAVY: str = "20/minute"   # for LLM-heavy endpoints

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ehs_user:password@localhost:5432/ehs_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── Embedding model (sentence-transformers) ──────────────────
    EMBED_MODEL_NAME: str = "all-MiniLM-L6-v2"
    HYBRID_VECTOR_THRESHOLD: float = 0.82
    HYBRID_TRGM_THRESHOLD: float = 0.45

    # ── pgvector / HNSW ──────────────────────────────────────────
    HNSW_M: int = 12
    HNSW_EF_CONSTRUCTION: int = 200
    HNSW_EF_SEARCH: int = 100
    VECTOR_SEARCH_TOP_K: int = 20

    # ── Quiz ─────────────────────────────────────────────────────
    QUIZ_NUM_QUESTIONS: int = 5
    QUIZ_MCQ_RATIO: float = 1.0

    # ── Groq ─────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"


settings = Settings()
