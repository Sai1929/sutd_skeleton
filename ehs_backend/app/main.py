"""FastAPI application factory."""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions import http_exception_handler, unhandled_exception_handler
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.auth_middleware import B2BAuthMiddleware
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import AsyncSessionLocal, close_engine, init_engine

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    log.info("app.starting", version=settings.APP_VERSION)

    # ── DB ──────────────────────────────────────────────────────
    try:
        await init_engine()
        app.state.db_available = True
        log.info("db.connected")
    except Exception as exc:
        app.state.db_available = False
        log.warning("db.unavailable", reason=str(exc))

    # ── Sentence-transformer embedding model ────────────────────
    embed_model = None
    try:
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer(settings.EMBED_MODEL_NAME)
        log.info("embed_model.loaded", name=settings.EMBED_MODEL_NAME)
    except Exception as exc:
        log.warning("embed_model.failed", reason=str(exc))

    # ── Hybrid lookup (pgvector + trgm + LLM fallback) ─────────
    if embed_model is not None and app.state.db_available:
        from app.services.recommendation.hybrid_lookup import HybridLookup
        app.state.hybrid_lookup = HybridLookup(embed_model, AsyncSessionLocal)
        log.info("hybrid_lookup.ready")
    else:
        app.state.hybrid_lookup = None
        log.warning(
            "hybrid_lookup.unavailable",
            embed_ok=embed_model is not None,
            db_ok=app.state.db_available,
            fallback="LLM direct generation",
        )

    # ── Groq client ─────────────────────────────────────────────
    if settings.GROQ_API_KEY:
        from app.services.chat.client import GroqChatClient
        app.state.chat_client = GroqChatClient()
        log.info("groq_client.ready", model=settings.GROQ_MODEL)
    else:
        app.state.chat_client = None
        log.warning("groq_client.skipped", reason="GROQ_API_KEY not set")

    log.info("app.ready")
    yield

    log.info("app.shutting_down")
    await close_engine()
    log.info("app.stopped")


_TAGS_METADATA = [
    {"name": "Req1 · Activity → RA JSON", "description": "Activity text → structured RA JSON (DB lookup + LLM fallback)"},
    {"name": "Req2 · Description → Word Doc RA", "description": "Project description → /generate returns RA JSON | /generate/docx downloads .docx"},
    {"name": "Req3 · Document → RA JSON", "description": "Upload .docx → extract + normalise → structured RA JSON"},
    {"name": "Req4 · RA → Compliance Quiz", "description": "RA details → generate mixed quiz (MCQ + descriptive + scenario)"},
    {"name": "Req5 · Hazard → Risk Controls", "description": "Text or image → identify hazard + risk level + control measures + mitigation activities"},
    {"name": "health", "description": "Health checks"},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_tags=_TAGS_METADATA,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Rate limiting ────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── Security headers ─────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)

    # ── B2B auth (X-API-Key + X-Student-ID) ─────────────────────
    app.add_middleware(B2BAuthMiddleware)

    # ── Request ID ──────────────────────────────────────────────
    app.add_middleware(RequestIDMiddleware)

    # ── CORS ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # ── Exception handlers ───────────────────────────────────────
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routers ──────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()
