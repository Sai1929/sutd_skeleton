"""
FastAPI application factory — Recommendation module only.
Lifespan: loads RecommendationEngine, connects to DB at startup.
"""
from contextlib import asynccontextmanager

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

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    log.info("app.starting", version=settings.APP_VERSION)

    # ── DB ──────────────────────────────────────────────────────
    await init_engine()
    log.info("db.connected")

    # ── Frequency recommendation engine (DB-backed) ─────────────
    rec_engine = RecommendationEngine()
    app.state.rec_engine = rec_engine
    log.info("rec_engine.ready")

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
