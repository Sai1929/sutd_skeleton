"""Generate structured RA JSON from extracted document content.

Combines data already present in the document with AI inference to fill
missing fields and normalise into the same schema as Req 1.
"""
import json

import structlog
from groq import AsyncGroq

from app.config import settings

log = structlog.get_logger()

_SYSTEM = """\
You are an EHS Risk Assessment Manager specialising in Singapore WSH regulations.

You will receive content extracted from an uploaded Word document that may contain
an existing or partial Risk Assessment. Your job is to:
1. Extract all RA rows already present in the document (from tables or text).
2. Infer and fill any missing fields using WSH knowledge.
3. Add rows to reach a minimum of 12 rows if fewer are present.
4. Normalise all data into this EXACT JSON schema:

{
  "project": "string — project/activity name from document",
  "assumptions": ["string — standard WSH assumptions, 6-7 items"],
  "rows": [
    {
      "main_activity": "string",
      "sub_activity": "string",
      "hazard": "string — specific named hazard",
      "consequences": "string — exact injury/damage outcome",
      "initial_l": number (1-5),
      "initial_s": number (1-5),
      "initial_risk": "string e.g. '15 (High)'",
      "control_measures": "string — hierarchy label + dash-bullet measures with inline SS/WSH refs",
      "residual_l": number (2-5, MINIMUM 2),
      "residual_s": number (1-5),
      "residual_risk": "string e.g. '8 (Medium)'"
    }
  ],
  "risk_matrix_note": "Likelihood (L): 1 Rare to 5 Almost Certain. Severity (S): 1 Minor to 5 Fatal. Risk = L x S. Bands: 1-4 Low | 5-9 Medium | 10-16 High | 17-25 Very High.",
  "chemical_note": "string",
  "references": ["string — Singapore WSH/NEA/SCDF source URLs only"]
}

HARD RULES:
- Minimum 12 rows. Add rows from the correct WSH activity checklist if document has fewer.
- Risk band MUST match score: 1-4=Low, 5-9=Medium, 10-16=High, 17-25=Very High.
- residual_l minimum is 2. Never set to 1 for administrative controls/PPE/procedures.
- Preserve all data found in the document. Only infer/fill what is missing.
- If the document already has control measures, keep them and add inline SS/WSH references.
- Respond with valid JSON only. No markdown, no explanation.
"""


async def generate_ra_from_document(doc_text: str, filename: str) -> dict:
    """Extract + normalise RA from document content into structured JSON."""
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    user_msg = (
        f"Document filename: {filename}\n\n"
        f"Extracted document content:\n\n{doc_text[:12000]}"
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=8192,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    log.info("doc_generator.done", filename=filename, rows=len(data.get("rows", [])))
    return data
