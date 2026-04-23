"""
BGE cross-encoder reranker (BAAI/bge-reranker-base).
Loaded once at startup; inference is CPU/GPU-bound and run via asyncio.to_thread.
"""
from __future__ import annotations

import asyncio

import structlog
from sentence_transformers import CrossEncoder

from app.config import settings
from app.services.rag.retrieval.vector_retriever import RetrievedChunk

log = structlog.get_logger()


class BGEReranker:
    def __init__(self) -> None:
        self._model: CrossEncoder | None = None

    async def load(self) -> None:
        log.info("reranker.loading", model=settings.RERANKER_MODEL)
        self._model = await asyncio.to_thread(
            CrossEncoder, settings.RERANKER_MODEL, max_length=512
        )
        log.info("reranker.loaded")

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def _rerank_sync(
        self, query: str, chunks: list[RetrievedChunk], top_k: int
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        pairs = [(query, c.chunk_text) for c in chunks]
        scores = self._model.predict(pairs, batch_size=settings.RERANKER_BATCH_SIZE)

        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        result = []
        for score, chunk in scored[:top_k]:
            chunk.score = float(score)
            result.append(chunk)
        return result

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        if self._model is None or not chunks:
            return chunks[: (top_k or settings.RERANKER_TOP_K)]

        k = top_k or settings.RERANKER_TOP_K
        return await asyncio.to_thread(self._rerank_sync, query, chunks, k)
