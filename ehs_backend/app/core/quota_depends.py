"""FastAPI dependency — quota check before endpoint, record after.

Usage in endpoint:
    @router.post("/recommend")
    async def recommend(body: ..., ctx: QuotaCtx = Depends(quota_dependency)):
        ...
        # after LLM call:
        await ctx.record(tokens_in=100, tokens_out=200)
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.quota.service import check_quota, record_usage


async def _get_db():
    async with AsyncSessionLocal() as session:
        yield session


@dataclass
class QuotaCtx:
    student_id: str
    endpoint: str
    _db: AsyncSession

    async def record(self, tokens_in: int, tokens_out: int) -> None:
        await record_usage(self._db, self.student_id, self.endpoint, tokens_in, tokens_out)


async def quota_dependency(request: Request, db: AsyncSession = Depends(_get_db)) -> QuotaCtx:
    student_id = getattr(request.state, "student_id", None)
    if not student_id:
        raise HTTPException(status_code=400, detail="Missing student identity.")

    allowed, used, limit = await check_quota(db, student_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily token quota exceeded.",
                "used": used,
                "limit": limit,
                "resets": "midnight SGT",
            },
        )

    return QuotaCtx(
        student_id=student_id,
        endpoint=request.url.path,
        _db=db,
    )
