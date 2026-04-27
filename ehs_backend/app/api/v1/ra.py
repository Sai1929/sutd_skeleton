"""Req2 · Description → RA JSON + Word document download."""
import io
import re
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.inspect import RARow, RecommendResponse
from app.services.ra.json_docx_writer import json_to_docx
from app.services.recommendation.ra_generator import generate_ra_json

router = APIRouter(prefix="/ra")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\- ]", "", name).strip().replace(" ", "_") or "risk_assessment"


@router.post(
    "/generate",
    tags=["Req2 · Description → Word Doc RA"],
    response_model=RecommendResponse,
)
async def generate_json(
    project_name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
) -> RecommendResponse:
    """Project description → structured full RA JSON."""
    project_text = description.strip() or project_name.strip()
    if not project_text:
        raise HTTPException(status_code=422, detail="Provide a project description or project name.")

    resolved_name = project_name.strip() or project_text
    ra_dict = await generate_ra_json(project_text)

    return RecommendResponse(
        activity=resolved_name,
        from_db=False,
        project=ra_dict.get("project", resolved_name),
        rows=[RARow(**r) for r in ra_dict.get("rows", [])],
        full_ra=ra_dict,
    )


@router.post(
    "/generate/docx",
    tags=["Req2 · Description → Word Doc RA"],
)
async def generate_docx(
    project_name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
) -> StreamingResponse:
    """Project description → generate full RA → download as .docx."""
    project_text = description.strip() or project_name.strip()
    if not project_text:
        raise HTTPException(status_code=422, detail="Provide a project description or project name.")

    resolved_name = project_name.strip() or "Untitled Project"
    ra_dict = await generate_ra_json(project_text)
    docx_bytes = json_to_docx(ra_dict, resolved_name)

    filename = _safe_filename(resolved_name) + ".docx"
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
