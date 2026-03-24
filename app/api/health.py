from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(request: Request) -> JSONResponse:
    checks: dict[str, str] = {}

    # DB check
    try:
        from sqlalchemy import text
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Rec engine check
    rec_engine = getattr(request.app.state, "rec_engine", None)
    checks["rec_engine"] = "ok" if (rec_engine and rec_engine.is_ready) else "not_loaded"

    # Reranker check
    reranker = getattr(request.app.state, "reranker", None)
    checks["reranker"] = "ok" if (reranker and reranker.is_ready) else "not_loaded"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
