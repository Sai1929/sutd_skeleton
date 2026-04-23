"""
FastAPI application factory.
Lifespan: loads ML models, connects to DB at startup.
"""
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions import http_exception_handler, unhandled_exception_handler
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.db.session import close_engine, init_engine
from app.services.recommendation.engine import RecommendationEngine
from app.services.chat.client import GroqChatClient

log = structlog.get_logger()


def _load_predictor():
    """Load trained DistilBERT predictor. Auto-detects shared vs per-step model."""
    model_dir = settings.DISTILBERT_MODEL_PATH
    if not Path(model_dir).exists():
        log.warning("predictor.skipped", reason=f"Model dir not found: {model_dir}")
        return None

    from app.ml.training.dataset import EHSDatasetBuilder
    label_vocab = EHSDatasetBuilder.load_vocab(model_dir)

    per_step_dir = Path(model_dir) / "step_hazard_type"
    if per_step_dir.exists():
        from app.ml.distilbert.predictor import EHSMultiStepPredictor
        predictor = EHSMultiStepPredictor.from_checkpoint(
            model_dir, label_vocab, device=settings.DISTILBERT_DEVICE
        )
        log.info("predictor.loaded", type="per_step", model_dir=model_dir)
    else:
        from app.ml.distilbert.predictor import EHSPredictor
        predictor = EHSPredictor.from_checkpoint(
            model_dir, label_vocab, device=settings.DISTILBERT_DEVICE
        )
        log.info("predictor.loaded", type="shared", model_dir=model_dir)

    return predictor


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

    # ── Frequency recommendation engine (DB-backed fallback) ────
    rec_engine = RecommendationEngine()
    app.state.rec_engine = rec_engine
    log.info("rec_engine.ready")

    # ── DistilBERT predictor (for /inspect/recommend) ───────────
    app.state.predictor = _load_predictor()

    # ── Groq chat client (risk assessment chatbot) ──────────────
    if settings.GROQ_API_KEY:
        app.state.chat_client = GroqChatClient()
        log.info("chat_client.ready", model=settings.GROQ_MODEL)
    else:
        app.state.chat_client = None
        log.warning("chat_client.skipped", reason="GROQ_API_KEY not set")

    log.info("app.ready")
    yield

    # ── Shutdown ────────────────────────────────────────────────
    log.info("app.shutting_down")
    await close_engine()
    log.info("app.stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware ───────────────────────────────────────────────
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ───────────────────────────────────────
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routers ──────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()
