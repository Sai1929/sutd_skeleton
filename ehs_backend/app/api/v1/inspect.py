from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.config import settings
from app.core.quota_depends import QuotaCtx, quota_dependency
from app.core.rate_limit import limiter
from app.schemas.inspect import RARow, RecommendRequest, RecommendResponse

router = APIRouter(prefix="/inspect")

_MAX_FILE_BYTES = 10 * 1024 * 1024


def _build_response(activity: str, ra_dict: dict, from_db: bool, include_full: bool = False) -> RecommendResponse:
    return RecommendResponse(
        activity=activity,
        from_db=from_db,
        project=ra_dict.get("project", ""),
        rows=[RARow(**r) for r in ra_dict.get("rows", [])],
        full_ra=ra_dict if include_full else None,
    )


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


@router.post("/recommend", tags=["Req1 · Activity → RA JSON"], response_model=RecommendResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def recommend(
    body: RecommendRequest,
    request: Request,
    ctx: QuotaCtx = Depends(quota_dependency),
) -> RecommendResponse:
    """Activity text → RA JSON (DB lookup + LLM fallback)."""
    if not body.activity.strip():
        raise HTTPException(status_code=422, detail="activity must not be empty")

    activity = body.activity.strip()
    lookup = getattr(request.app.state, "hybrid_lookup", None)

    if lookup is not None:
        ra_dict, from_db = await lookup.lookup(activity)
    else:
        if not settings.GROQ_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="Service unavailable: no database and no GROQ_API_KEY configured.",
            )
        from app.services.recommendation.ra_generator import generate_ra_json
        ra_dict = await generate_ra_json(activity)
        from_db = False

    import json
    response_text = json.dumps(ra_dict)
    await ctx.record(
        tokens_in=_estimate_tokens(activity),
        tokens_out=_estimate_tokens(response_text),
    )

    return _build_response(activity, ra_dict, from_db)


@router.post("/from-document", tags=["Req3 · Document → RA JSON"], response_model=RecommendResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def from_document(
    request: Request,
    ctx: QuotaCtx = Depends(quota_dependency),
    file: UploadFile = File(..., description="Word document (.docx) containing RA data"),
) -> RecommendResponse:
    """Upload .docx → extract RA data → normalise to JSON."""
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(status_code=422, detail="Only .docx files supported.")
    data = await file.read()
    if len(data) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit.")

    from app.services.ra.extractor import extract_docx_full
    from app.services.recommendation.doc_generator import generate_ra_from_document

    doc_text = extract_docx_full(data)
    if not doc_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from document.")

    ra_dict = await generate_ra_from_document(doc_text, file.filename or "upload.docx")
    activity = ra_dict.get("project", file.filename or "Uploaded Document")

    import json
    await ctx.record(
        tokens_in=_estimate_tokens(doc_text),
        tokens_out=_estimate_tokens(json.dumps(ra_dict)),
    )

    return _build_response(activity, ra_dict, from_db=False, include_full=True)
