"""
Intent classifier — routes queries to structured (self-query) or vague (HyDE) pipeline.
Uses fast regex/keyword rules first; falls back to GPT-4o mini for ambiguous cases.
"""
from __future__ import annotations

import re
from enum import Enum

from openai import AsyncAzureOpenAI

from app.config import settings

# Patterns that signal a structured / analytical query
STRUCTURED_PATTERNS = [
    r"\bhow many\b",
    r"\bcount\b",
    r"\btotal\b",
    r"\bnumber of\b",
    r"\blist\b.{0,20}\b(request|submission|incident)\b",
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    r"\b\d{4}\b",  # 4-digit year
    r"\b(last|this|past)\s+(week|month|year)\b",
    r"\bmost\s+common\b",
    r"\bwhich\s+activity\b",
    r"\b(latest|most recent|newest|recently|recent)\b",  # recency queries
]

VAGUE_PATTERNS = [
    r"\bwhat\s+is\b",
    r"\bexplain\b",
    r"\bdescribe\b",
    r"\bhow\s+to\b",
    r"\bwhy\b",
    r"\bwhat\s+are\s+the\b",
]


class QueryIntent(str, Enum):
    STRUCTURED = "structured"   # has date/count/filter → self-querying
    VAGUE = "vague"             # semantic domain query → HyDE
    HYBRID = "hybrid"           # both signals → self-query + HyDE


class IntentClassifier:
    def __init__(self, client: AsyncAzureOpenAI | None = None) -> None:
        self._client = client

    def classify_fast(self, query: str) -> QueryIntent | None:
        q = query.lower()
        has_structured = any(re.search(p, q) for p in STRUCTURED_PATTERNS)
        has_vague = any(re.search(p, q) for p in VAGUE_PATTERNS)

        if has_structured and has_vague:
            return QueryIntent.HYBRID
        if has_structured:
            return QueryIntent.STRUCTURED
        if has_vague:
            return QueryIntent.VAGUE
        return None  # ambiguous — needs LLM

    async def classify(self, query: str) -> QueryIntent:
        fast = self.classify_fast(query)
        if fast is not None:
            return fast

        if self._client is None:
            return QueryIntent.HYBRID

        prompt = (
            "Classify this EHS chatbot query into one of: structured, vague, hybrid.\n"
            "structured = counting/filtering/date-based queries\n"
            "vague = open-ended semantic questions\n"
            "hybrid = both\n"
            f"Query: {query}\n"
            "Reply with ONLY one word: structured, vague, or hybrid."
        )
        resp = await self._client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        raw = resp.choices[0].message.content.strip().lower()
        if "structured" in raw:
            return QueryIntent.STRUCTURED
        if "vague" in raw:
            return QueryIntent.VAGUE
        return QueryIntent.HYBRID
