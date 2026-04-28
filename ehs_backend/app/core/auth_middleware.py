"""B2B auth middleware — validates X-API-Key + extracts X-Student-ID."""
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

log = structlog.get_logger()

# Paths that skip auth (health checks, docs)
_EXEMPT_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json")


class B2BAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for exempt paths
        if any(request.url.path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-API-Key", "")
        if api_key != settings.B2B_API_KEY:
            log.warning("auth.invalid_api_key", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing X-API-Key."},
            )

        # Extract student ID
        student_id = request.headers.get("X-Student-ID", "").strip()
        if not student_id:
            log.warning("auth.missing_student_id", path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing X-Student-ID header."},
            )

        # Attach to request state for use in endpoints
        request.state.student_id = student_id
        return await call_next(request)
