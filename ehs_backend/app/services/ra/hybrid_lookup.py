"""Hybrid DB lookup for Risk Assessments.

Search order:
  1. pgvector cosine similarity (semantic)   >= HYBRID_VECTOR_THRESHOLD (0.82)
  2. pg_trgm trigram similarity (fuzzy text) >= HYBRID_TRGM_THRESHOLD   (0.45)
  3. Miss → generate via LLM → save to DB
"""
import re

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.services.ra.generator import generate_ra

log = structlog.get_logger()


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


class RAHybridLookup:
    def __init__(self, embed_model, session_factory: async_sessionmaker):
        self._embed = embed_model
        self._factory = session_factory

    async def lookup(self, project_input: str, project_name: str) -> tuple[str, bool]:
        """Return (ra_markdown, from_db)."""
        normalized = _normalize(project_input)
        embedding = self._embed.encode(project_input, normalize_embeddings=True).tolist()
        emb_str = "[" + ",".join(str(x) for x in embedding) + "]"

        async with self._factory() as session:
            # 1. Vector search
            row = await _vector_search(session, emb_str)
            if row:
                log.info("ra_lookup.vector_hit", id=row.id)
                return row.ra_markdown, True

            # 2. Trigram search
            row = await _trgm_search(session, normalized)
            if row:
                log.info("ra_lookup.trgm_hit", id=row.id)
                return row.ra_markdown, True

            # 3. LLM generation + save
            log.info("ra_lookup.miss", project=project_name)
            ra_markdown = await generate_ra(project_input, project_name)
            await _save(session, project_input, normalized, project_name, emb_str, ra_markdown)
            return ra_markdown, False


async def _vector_search(session: AsyncSession, emb_str: str):
    sql = text("""
        SELECT id, ra_markdown,
               1 - (embedding <=> CAST(:emb AS vector)) AS score
        FROM risk_assessments
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> CAST(:emb AS vector)) >= :threshold
        ORDER BY score DESC
        LIMIT 1
    """)
    result = await session.execute(sql, {"emb": emb_str, "threshold": settings.HYBRID_VECTOR_THRESHOLD})
    return result.fetchone()


async def _trgm_search(session: AsyncSession, normalized: str):
    sql = text("""
        SELECT id, ra_markdown,
               similarity(project_input_normalized, :q) AS score
        FROM risk_assessments
        WHERE similarity(project_input_normalized, :q) >= :threshold
        ORDER BY score DESC
        LIMIT 1
    """)
    result = await session.execute(sql, {"q": normalized, "threshold": settings.HYBRID_TRGM_THRESHOLD})
    return result.fetchone()


async def _save(
    session: AsyncSession,
    project_input: str,
    normalized: str,
    project_name: str,
    emb_str: str,
    ra_markdown: str,
) -> None:
    sql = text("""
        INSERT INTO risk_assessments
            (project_input, project_input_normalized, project_name, embedding, ra_markdown)
        VALUES
            (:project_input, :normalized, :project_name, CAST(:emb AS vector), :ra_markdown)
        RETURNING id
    """)
    result = await session.execute(sql, {
        "project_input": project_input,
        "normalized": normalized,
        "project_name": project_name,
        "emb": emb_str,
        "ra_markdown": ra_markdown,
    })
    await session.commit()
    row = result.fetchone()
    log.info("ra_lookup.saved", id=row.id if row else None)
