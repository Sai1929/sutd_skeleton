from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.config import settings
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


@router.post("/recommend", tags=["Req1 · Activity → RA JSON"], response_model=RecommendResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    """Activity text → RA JSON (DB lookup + LLM fallback)."""
    if not body.activity.strip():
        raise HTTPException(status_code=422, detail="activity must not be empty")

    activity = body.activity.strip()
    lookup = getattr(request.app.state, "hybrid_lookup", None)

    if lookup is not None:
        ra_dict, from_db = await lookup.lookup(activity)
    else:
        # No DB/embed — fall back to direct LLM generation
        if not settings.GROQ_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="Service unavailable: no database and no GROQ_API_KEY configured.",
            )
        from app.services.recommendation.ra_generator import generate_ra_json
        ra_dict = await generate_ra_json(activity)
        from_db = False

    return _build_response(activity, ra_dict, from_db)


@router.post("/from-document", tags=["Req3 · Document → RA JSON"], response_model=RecommendResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def from_document(
    request: Request,
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
    return _build_response(activity, ra_dict, from_db=False, include_full=True)
