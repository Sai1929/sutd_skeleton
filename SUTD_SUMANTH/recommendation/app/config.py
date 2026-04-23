from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "EHS Inspection API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ehs_user:password@localhost:5432/ehs_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── Session / conversation cleanup thresholds ────────────────
    SESSION_TTL_SECONDS: int = 3600   # stale sessions deleted after this many seconds
    CONV_TTL_SECONDS: int = 7200      # stale conversations deleted after this many seconds
    CONV_MAX_TURNS: int = 10          # sliding window: keep last N human+ai turn pairs

    # ── Azure OpenAI ─────────────────────────────────────────────
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-4o-mini"
    AZURE_OPENAI_EMBED_DEPLOYMENT: str = "text-embedding-3-small"
    AZURE_OPENAI_EMBED_DIMS: int = 1536

    # ── DistilBERT ───────────────────────────────────────────────
    DISTILBERT_MODEL_PATH: str = "./models/ehs_distilbert"
    DISTILBERT_MAX_SEQ_LEN: int = 128
    DISTILBERT_BATCH_SIZE: int = 32
    DISTILBERT_DEVICE: str = "cpu"
    DISTILBERT_TOP_K_OPTIONS: int = 10

    # ── pgvector / HNSW ──────────────────────────────────────────
    HNSW_M: int = 12
    HNSW_EF_CONSTRUCTION: int = 200
    HNSW_EF_SEARCH: int = 100
    VECTOR_SEARCH_TOP_K: int = 20

    # ── BM25 ─────────────────────────────────────────────────────
    BM25_SEARCH_TOP_K: int = 20

    # ── RRF ──────────────────────────────────────────────────────
    RRF_K: int = 60

    # ── Reranker ─────────────────────────────────────────────────
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    RERANKER_TOP_K: int = 5
    RERANKER_BATCH_SIZE: int = 32

    # ── Chunking ─────────────────────────────────────────────────
    CHUNK_TARGET_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 50

    # ── Quiz ─────────────────────────────────────────────────────
    QUIZ_NUM_QUESTIONS: int = 5
    QUIZ_MCQ_RATIO: float = 0.6

    # ── Embedding batching ───────────────────────────────────────
    EMBED_BATCH_SIZE: int = 16
    EMBED_MAX_RETRIES: int = 3
    EMBED_RETRY_BASE_DELAY: float = 1.0


settings = Settings()
