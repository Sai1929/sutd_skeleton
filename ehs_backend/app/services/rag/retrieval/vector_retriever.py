"""pgvector HNSW ANN retriever."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


def _to_date(val) -> date:
    """Convert a string 'YYYY-MM-DD' or date/datetime to a date object."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    return datetime.strptime(val, "%Y-%m-%d").date()


@dataclass
class RetrievedChunk:
    id: int
    chunk_text: str
    source_type: str
    source_id: str
    activity_name: str | None
    hazard_type: str | None
    submitted_at: str | None
    score: float  # cosine similarity (higher = more relevant)


class VectorRetriever:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        k = top_k or settings.VECTOR_SEARCH_TOP_K
        ef_search = settings.HNSW_EF_SEARCH

        # Build WHERE clause from filters
        where_clauses = ["embedding IS NOT NULL"]
        params: dict = {"embedding": str(query_embedding.tolist()), "k": k}

        if filters:
            if filters.get("activity_name"):
                where_clauses.append("activity_name = :activity_name")
                params["activity_name"] = filters["activity_name"]
            if filters.get("hazard_type"):
                where_clauses.append("hazard_type = :hazard_type")
                params["hazard_type"] = filters["hazard_type"]
            if filters.get("submitted_at__gte"):
                where_clauses.append("submitted_at >= :date_from")
                params["date_from"] = _to_date(filters["submitted_at__gte"])
            if filters.get("submitted_at__lte"):
                where_clauses.append("submitted_at <= :date_to")
                params["date_to"] = _to_date(filters["submitted_at__lte"])

        where_str = " AND ".join(where_clauses)

        # SET LOCAL doesn't accept bound params — inline the value
        await self._db.execute(text(f"SET LOCAL hnsw.ef_search = {ef_search}"))

        sql = text(f"""
            SELECT
                id,
                chunk_text,
                source_type,
                source_id::text,
                activity_name,
                hazard_type,
                submitted_at::text,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM document_chunks
            WHERE {where_str}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :k
        """)

        result = await self._db.execute(sql, params)
        rows = result.fetchall()

        return [
            RetrievedChunk(
                id=r.id,
                chunk_text=r.chunk_text,
                source_type=r.source_type,
                source_id=r.source_id,
                activity_name=r.activity_name,
                hazard_type=r.hazard_type,
                submitted_at=r.submitted_at,
                score=float(r.score),
            )
            for r in rows
        ]
