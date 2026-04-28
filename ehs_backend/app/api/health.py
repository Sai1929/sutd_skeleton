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
    if getattr(request.app.state, "db_available", False):
        try:
            from sqlalchemy import text
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"
    else:
        checks["database"] = "unavailable"

    # Hybrid lookup (Req1)
    lookup = getattr(request.app.state, "hybrid_lookup", None)
    checks["hybrid_lookup"] = "ok" if lookup is not None else "unavailable (LLM fallback active)"

    # Groq (Req2, Req4, Req5)
    groq = getattr(request.app.state, "chat_client", None)
    checks["groq"] = "ok" if groq is not None else "unavailable"

    # Service is ready if Groq is available (LLM is the core dependency)
    critical_ok = checks["groq"] == "ok"
    status_code = 200 if critical_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if critical_ok else "degraded", "checks": checks},
    )
