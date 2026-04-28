"""Per-student daily token quota — backed by Postgres."""
import datetime

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

log = structlog.get_logger()


async def get_usage_today(db: AsyncSession, student_id: str) -> int:
    """Return tokens used today for this student. 0 if no row yet."""
    result = await db.execute(
        text(
            "SELECT tokens_used FROM token_budgets "
            "WHERE student_id = :sid AND date = CURRENT_DATE"
        ),
        {"sid": student_id},
    )
    row = result.fetchone()
    return row.tokens_used if row else 0


async def check_quota(db: AsyncSession, student_id: str) -> tuple[bool, int, int]:
    """
    Returns (allowed, used, limit).
    allowed=False means quota exceeded — return 429.
    """
    used = await get_usage_today(db, student_id)
    limit = settings.TOKEN_DAILY_LIMIT
    return used < limit, used, limit


async def record_usage(
    db: AsyncSession,
    student_id: str,
    endpoint: str,
    tokens_in: int,
    tokens_out: int,
) -> None:
    """Atomically increment daily budget + insert audit row."""
    total = tokens_in + tokens_out

    # Upsert daily counter
    await db.execute(
        text("""
            INSERT INTO token_budgets (student_id, date, tokens_used)
            VALUES (:sid, CURRENT_DATE, :total)
            ON CONFLICT (student_id, date)
            DO UPDATE SET tokens_used = token_budgets.tokens_used + EXCLUDED.tokens_used
        """),
        {"sid": student_id, "total": total},
    )

    # Audit log
    await db.execute(
        text("""
            INSERT INTO token_usage_log (student_id, endpoint, tokens_in, tokens_out)
            VALUES (:sid, :endpoint, :tin, :tout)
        """),
        {"sid": student_id, "endpoint": endpoint, "tin": tokens_in, "tout": tokens_out},
    )

    await db.commit()
    log.info("quota.recorded", student_id=student_id, endpoint=endpoint, tokens=total)
