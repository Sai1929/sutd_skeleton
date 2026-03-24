"""
SemanticChunker — sentence-aware chunking using spaCy.
Target: 400 tokens per chunk, 50-token overlap.
"""
from __future__ import annotations

from dataclasses import dataclass

import spacy

# Lazy-load spaCy model
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        _nlp.add_pipe("sentencizer")
    return _nlp


@dataclass
class ChunkData:
    chunk_index: int
    text: str
    token_count: int
    metadata: dict


class SemanticChunker:
    def __init__(
        self,
        target_tokens: int = 400,
        overlap_tokens: int = 50,
    ) -> None:
        self.target = target_tokens
        self.overlap = overlap_tokens

    def chunk(self, text: str, metadata: dict | None = None) -> list[ChunkData]:
        """
        Split text into overlapping chunks at sentence boundaries.
        Returns list of ChunkData objects.
        """
        nlp = _get_nlp()
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        if not sentences:
            return []

        # Short documents: single chunk
        total_tokens = len(text.split())
        if total_tokens <= self.target:
            return [ChunkData(0, text, total_tokens, metadata or {})]

        chunks: list[ChunkData] = []
        current_sents: list[str] = []
        current_tokens = 0
        chunk_idx = 0

        for sent in sentences:
            sent_tokens = len(sent.split())

            if current_tokens + sent_tokens > self.target and current_sents:
                # Emit current chunk
                chunk_text = " ".join(current_sents)
                chunks.append(
                    ChunkData(chunk_idx, chunk_text, current_tokens, metadata or {})
                )
                chunk_idx += 1

                # Build overlap: keep trailing sentences that fit within overlap budget
                overlap_sents: list[str] = []
                overlap_count = 0
                for s in reversed(current_sents):
                    s_tok = len(s.split())
                    if overlap_count + s_tok <= self.overlap:
                        overlap_sents.insert(0, s)
                        overlap_count += s_tok
                    else:
                        break

                current_sents = overlap_sents
                current_tokens = overlap_count

            current_sents.append(sent)
            current_tokens += sent_tokens

        # Emit any remaining sentences
        if current_sents:
            chunk_text = " ".join(current_sents)
            chunks.append(
                ChunkData(chunk_idx, chunk_text, current_tokens, metadata or {})
            )

        return chunks
