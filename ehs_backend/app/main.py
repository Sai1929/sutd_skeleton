"""
FastAPI application factory.
Lifespan: loads all ML models, connects to DB + Redis at startup.
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import AzureChatOpenAI
from openai import AsyncAzureOpenAI

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions import http_exception_handler, unhandled_exception_handler
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.db.session import close_engine, init_engine
from app.services.recommendation.engine import RecommendationEngine
from app.services.rag.retrieval.reranker import BGEReranker
from app.services.rag.chain import HybridRAGChain

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    log.info("app.starting", version=settings.APP_VERSION)

    # ── DB ──────────────────────────────────────────────────────
    await init_engine()
    log.info("db.connected")

    # ── Azure OpenAI client ─────────────────────────────────────
    azure_client = AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )
    app.state.azure_llm = azure_client

    # LangChain AzureChatOpenAI for LCEL chain
    langchain_llm = AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
        temperature=0.7,
        streaming=False,
    )

    # ── Frequency recommendation engine (no model — DB-backed) ──
    rec_engine = RecommendationEngine()
    app.state.rec_engine = rec_engine
    log.info("rec_engine.ready")

    # ── BGE Reranker ────────────────────────────────────────────
    reranker = BGEReranker()
    await reranker.load()
    app.state.reranker = reranker

    # ── RAG chain (prototype — DB session injected per-request) ─
    # We store components on app.state; the actual chain is built per request
    # in the chatbot router to get the request-scoped DB session.
    app.state.rag_chain = HybridRAGChain(
        azure_client=azure_client,
        langchain_llm=langchain_llm,
        reranker=reranker,
        db=None,       # placeholder — overridden per request
    )
    app.state.azure_embedder = azure_client

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
        allow_origins=["*"],  # Tighten in production
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
