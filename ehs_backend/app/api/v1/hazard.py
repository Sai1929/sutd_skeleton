"""Req5 · Hazard Analysis — text or image → risk control measures."""
import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.config import settings
from app.core.quota_depends import QuotaCtx, quota_dependency
from app.core.rate_limit import limiter
from app.schemas.hazard import HazardAnalysisResponse
from app.services.hazard.analyser import analyse_hazard

router = APIRouter(prefix="/hazard")

_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post(
    "/analyse",
    tags=["Req5 · Hazard → Risk Controls"],
    response_model=HazardAnalysisResponse,
)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def analyse(
    request: Request,
    ctx: QuotaCtx = Depends(quota_dependency),
    text: Annotated[str, Form()] = "",
    image: Annotated[UploadFile | None, File()] = None,
) -> HazardAnalysisResponse:
    """Text description and/or image → identified hazard + control measures + mitigation activities."""
    if not text.strip() and image is None:
        raise HTTPException(status_code=422, detail="Provide text, image, or both.")

    image_b64: str | None = None
    image_mime = "image/jpeg"
    image_bytes_len = 0

    if image is not None:
        mime = image.content_type or "image/jpeg"
        if mime not in _ALLOWED_MIME:
            raise HTTPException(status_code=422, detail=f"Unsupported image type: {mime}. Use JPEG, PNG, or WebP.")
        data = await image.read()
        if len(data) > _MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit.")
        image_b64 = base64.b64encode(data).decode()
        image_mime = mime
        image_bytes_len = len(data)

    result = await analyse_hazard(
        text=text.strip() or None,
        image_b64=image_b64,
        image_mime=image_mime,
    )

    # Images count ~85 tokens per 512px tile — use byte size as rough proxy
    image_tokens = image_bytes_len // 1000 if image_bytes_len else 0
    await ctx.record(
        tokens_in=max(1, len(text) // 4) + image_tokens,
        tokens_out=max(1, len(json.dumps(result.model_dump())) // 4),
    )

    return result
