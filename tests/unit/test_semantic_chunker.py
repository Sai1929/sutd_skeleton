"""Unit tests for SemanticChunker."""
import pytest
from app.services.rag.ingestion.chunker import SemanticChunker


def test_short_doc_single_chunk():
    chunker = SemanticChunker(target_tokens=400, overlap_tokens=50)
    text = "This is a short document."
    chunks = chunker.chunk(text)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0


def test_long_doc_multiple_chunks():
    chunker = SemanticChunker(target_tokens=20, overlap_tokens=5)
    # Create a document that will definitely exceed 20 tokens
    text = ". ".join([f"This is sentence number {i} about welding safety" for i in range(30)])
    chunks = chunker.chunk(text)
    assert len(chunks) > 1


def test_chunks_have_sequential_indexes():
    chunker = SemanticChunker(target_tokens=20, overlap_tokens=5)
    text = ". ".join([f"EHS safety sentence {i}" for i in range(40)])
    chunks = chunker.chunk(text)
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_metadata_propagated():
    chunker = SemanticChunker()
    meta = {"activity_name": "Welding", "hazard_type": "Arc Flash"}
    chunks = chunker.chunk("Short text.", metadata=meta)
    assert chunks[0].metadata == meta


def test_empty_text():
    chunker = SemanticChunker()
    assert chunker.chunk("") == []
