"""Unit tests for RRFFusion."""
import pytest
from app.services.rag.retrieval.rrf_fusion import RRFFusion
from app.services.rag.retrieval.vector_retriever import RetrievedChunk


def make_chunk(id: int, score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        id=id,
        chunk_text=f"chunk {id}",
        source_type="inspection_submission",
        source_id="test-uuid",
        activity_name="Welding",
        hazard_type="Arc Flash",
        submitted_at=None,
        score=score,
    )


def test_rrf_deduplicates():
    rrf = RRFFusion(k=60)
    vec_results = [make_chunk(1, 0.9), make_chunk(2, 0.8), make_chunk(3, 0.7)]
    bm25_results = [make_chunk(2, 0.95), make_chunk(1, 0.85), make_chunk(4, 0.6)]

    fused = rrf.fuse(vec_results, bm25_results, top_k=10)
    ids = [c.id for c in fused]

    # No duplicates
    assert len(ids) == len(set(ids))


def test_rrf_score_order():
    """Chunk appearing in both lists should rank higher than chunk in one."""
    rrf = RRFFusion(k=60)
    # chunk 1 appears in both lists at rank 1
    vec_results = [make_chunk(1), make_chunk(3)]
    bm25_results = [make_chunk(1), make_chunk(2)]

    fused = rrf.fuse(vec_results, bm25_results, top_k=10)
    assert fused[0].id == 1, "Chunk in both lists should rank first"


def test_rrf_top_k_respected():
    rrf = RRFFusion(k=60)
    vec = [make_chunk(i) for i in range(15)]
    bm25 = [make_chunk(i + 10) for i in range(15)]

    fused = rrf.fuse(vec, bm25, top_k=5)
    assert len(fused) == 5


def test_rrf_empty_inputs():
    rrf = RRFFusion(k=60)
    assert rrf.fuse([], [], top_k=10) == []
    assert rrf.fuse([make_chunk(1)], [], top_k=10) != []
