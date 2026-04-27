from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from app.schemas.inspect import RARow, RecommendRequest, RecommendResponse

router = APIRouter(prefix="/inspect")

_MAX_FILE_BYTES = 10 * 1024 * 1024


def _build_response(activity: str, ra_dict: dict, from_db: bool, include_full: bool = False) -> RecommendResponse:
    return RecommendResponse(
        activity=activity,
        from_db=from_db,
        project=ra_dict.get("project", ""),
        assumptions=ra_dict.get("assumptions", []),
        rows=[RARow(**r) for r in ra_dict.get("rows", [])],
        full_ra=ra_dict if include_full else None,
    )


@router.post("/recommend", tags=["Req1 · Activity → RA JSON"], response_model=RecommendResponse)
async def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    """Activity text → RA JSON (DB lookup + LLM fallback)."""
    if not body.activity.strip():
        raise HTTPException(status_code=422, detail="activity must not be empty")
    lookup = request.app.state.hybrid_lookup
    ra_dict, from_db = await lookup.lookup(body.activity.strip())
    return _build_response(body.activity.strip(), ra_dict, from_db)


@router.post("/from-document", tags=["Req3 · Document → RA JSON"], response_model=RecommendResponse)
async def from_document(
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
