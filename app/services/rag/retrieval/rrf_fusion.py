"""Reciprocal Rank Fusion (k=60) — fuses dense and sparse retrieval results."""
from __future__ import annotations

from app.config import settings
from app.services.rag.retrieval.vector_retriever import RetrievedChunk


class RRFFusion:
    def __init__(self, k: int | None = None) -> None:
        self._k = k or settings.RRF_K

    def fuse(
        self,
        vector_results: list[RetrievedChunk],
        bm25_results: list[RetrievedChunk],
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """
        Compute RRF score for each chunk across both ranked lists.
        rrf_score(i) = 1/(k + rank_in_vector) + 1/(k + rank_in_bm25)
        Chunks in only one list get rank = len(list)+1 in the other.
        """
        k = self._k

        # Build id → chunk map (vector results take priority for metadata)
        chunk_map: dict[int, RetrievedChunk] = {}
        for c in vector_results:
            chunk_map[c.id] = c
        for c in bm25_results:
            if c.id not in chunk_map:
                chunk_map[c.id] = c

        scores: dict[int, float] = {cid: 0.0 for cid in chunk_map}

        for rank, chunk in enumerate(vector_results, start=1):
            scores[chunk.id] += 1.0 / (k + rank)

        for rank, chunk in enumerate(bm25_results, start=1):
            scores[chunk.id] += 1.0 / (k + rank)

        # Sort by RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        results: list[RetrievedChunk] = []
        for cid in sorted_ids[:top_k]:
            chunk = chunk_map[cid]
            chunk.score = scores[cid]  # replace raw scores with RRF score
            results.append(chunk)

        return results
