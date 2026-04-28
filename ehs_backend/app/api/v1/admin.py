"""Admin — token usage reporting."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

router = APIRouter(prefix="/admin", tags=["admin"])


class StudentUsage(BaseModel):
    student_id: str
    date: str
    tokens_used: int


class UsageSummary(BaseModel):
    student_id: str
    total_tokens: int
    days_active: int
    last_active: str | None


@router.get("/usage", response_model=list[UsageSummary])
async def all_usage(days: int = 30) -> list[UsageSummary]:
    """All students — token usage summary for last N days."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT
                    student_id,
                    SUM(tokens_used) AS total_tokens,
                    COUNT(DISTINCT date) AS days_active,
                    MAX(date)::text AS last_active
                FROM token_budgets
                WHERE date >= CURRENT_DATE - :days
                GROUP BY student_id
                ORDER BY total_tokens DESC
            """),
            {"days": days},
        )
        rows = result.fetchall()
    return [
        UsageSummary(
            student_id=r.student_id,
            total_tokens=r.total_tokens,
            days_active=r.days_active,
            last_active=r.last_active,
        )
        for r in rows
    ]


@router.get("/usage/{student_id}", response_model=list[StudentUsage])
async def student_usage(student_id: str, days: int = 30) -> list[StudentUsage]:
    """Single student — daily breakdown for last N days."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT student_id, date::text AS date, tokens_used
                FROM token_budgets
                WHERE student_id = :sid
                  AND date >= CURRENT_DATE - :days
                ORDER BY date DESC
            """),
            {"sid": student_id, "days": days},
        )
        rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No usage data for student: {student_id}")

    return [StudentUsage(student_id=r.student_id, date=r.date, tokens_used=r.tokens_used) for r in rows]


@router.delete("/usage/{student_id}/reset")
async def reset_quota(student_id: str) -> dict:
    """Reset today's quota for a student (admin override)."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM token_budgets WHERE student_id = :sid AND date = CURRENT_DATE"),
            {"sid": student_id},
        )
        await db.commit()
    return {"detail": f"Quota reset for {student_id} today."}
