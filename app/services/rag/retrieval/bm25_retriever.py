"""PostgreSQL full-text (BM25) retriever using ts_vector + GIN index."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.rag.retrieval.vector_retriever import RetrievedChunk


class BM25Retriever:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        k = top_k or settings.BM25_SEARCH_TOP_K

        where_clauses = ["ts_vector @@ plainto_tsquery('english', :query)"]
        params: dict = {"query": query, "k": k}

        if filters:
            if filters.get("activity_name"):
                where_clauses.append("activity_name = :activity_name")
                params["activity_name"] = filters["activity_name"]
            if filters.get("hazard_type"):
                where_clauses.append("hazard_type = :hazard_type")
                params["hazard_type"] = filters["hazard_type"]
            if filters.get("submitted_at__gte"):
                where_clauses.append("submitted_at >= :date_from")
                params["date_from"] = filters["submitted_at__gte"]
            if filters.get("submitted_at__lte"):
                where_clauses.append("submitted_at <= :date_to")
                params["date_to"] = filters["submitted_at__lte"]

        where_str = " AND ".join(where_clauses)

        sql = text(f"""
            SELECT
                id,
                chunk_text,
                source_type,
                source_id::text,
                activity_name,
                hazard_type,
                submitted_at::text,
                ts_rank_cd(ts_vector, plainto_tsquery('english', :query)) AS score
            FROM document_chunks
            WHERE {where_str}
            ORDER BY score DESC
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
