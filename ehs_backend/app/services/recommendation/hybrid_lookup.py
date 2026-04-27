"""Hybrid DB lookup for activity RA JSON.

Search order:
  1. pgvector cosine similarity  >= HYBRID_VECTOR_THRESHOLD (0.82)
  2. pg_trgm trigram similarity  >= HYBRID_TRGM_THRESHOLD   (0.45)
  3. Miss → generate full RA JSON via LLM → save to DB
"""
import json
import re

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.services.recommendation.ra_generator import generate_ra_json

log = structlog.get_logger()


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


class HybridLookup:
    def __init__(self, embed_model, session_factory: async_sessionmaker):
        self._embed = embed_model
        self._factory = session_factory

    async def lookup(self, activity: str) -> tuple[dict, bool]:
        """Return (ra_json_dict, from_db)."""
        normalized = _normalize(activity)
        embedding = self._embed.encode(activity, normalize_embeddings=True).tolist()
        emb_str = "[" + ",".join(str(x) for x in embedding) + "]"

        async with self._factory() as session:
            row = await _vector_search(session, emb_str)
            if row:
                log.info("hybrid_lookup.hit", id=row.id, method="vector")
                ra = row.ra_json if isinstance(row.ra_json, dict) else json.loads(row.ra_json)
                return ra, True

            row = await _trgm_search(session, normalized)
            if row:
                log.info("hybrid_lookup.hit", id=row.id, method="trgm")
                ra = row.ra_json if isinstance(row.ra_json, dict) else json.loads(row.ra_json)
                return ra, True

            log.info("hybrid_lookup.miss", activity=activity)
            ra_dict = await generate_ra_json(activity)
            await _save(session, activity, normalized, emb_str, ra_dict)
            return ra_dict, False


async def _vector_search(session: AsyncSession, emb_str: str):
    sql = text("""
        SELECT id, ra_json,
               1 - (embedding <=> CAST(:emb AS vector)) AS score
        FROM activity_recommendations
        WHERE embedding IS NOT NULL
          AND ra_json IS NOT NULL
          AND 1 - (embedding <=> CAST(:emb AS vector)) >= :threshold
        ORDER BY score DESC
        LIMIT 1
    """)
    result = await session.execute(sql, {
        "emb": emb_str,
        "threshold": settings.HYBRID_VECTOR_THRESHOLD,
    })
    return result.fetchone()


async def _trgm_search(session: AsyncSession, normalized: str):
    sql = text("""
        SELECT id, ra_json,
               similarity(activity_normalized, :q) AS score
        FROM activity_recommendations
        WHERE ra_json IS NOT NULL
          AND similarity(activity_normalized, :q) >= :threshold
        ORDER BY score DESC
        LIMIT 1
    """)
    result = await session.execute(sql, {
        "q": normalized,
        "threshold": settings.HYBRID_TRGM_THRESHOLD,
    })
    return result.fetchone()


async def _save(
    session: AsyncSession,
    activity: str,
    normalized: str,
    emb_str: str,
    ra_dict: dict,
) -> None:
    ra_json_str = json.dumps(ra_dict)
    sql = text("""
        INSERT INTO activity_recommendations
            (activity_input, activity_normalized, embedding,
             hazard_types, severity_likelihood, moc_ppe, remarks, ra_json)
        VALUES
            (:activity, :normalized, CAST(:emb AS vector),
             ARRAY[]::text[], '', '', '', CAST(:ra_json AS jsonb))
        RETURNING id
    """)
    result = await session.execute(sql, {
        "activity": activity,
        "normalized": normalized,
        "emb": emb_str,
        "ra_json": ra_json_str,
    })
    await session.commit()
    row = result.fetchone()
    log.info("hybrid_lookup.saved", id=row.id if row else None)
