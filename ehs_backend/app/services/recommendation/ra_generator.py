"""Generate full structured RA JSON for an activity using Groq JSON mode.

Same WSH compliance rules as chatbot system prompt — minimum 12 rows,
residual L >= 2, SS references inline, Singapore regulations.
Output is structured JSON (not markdown).
"""
import json

import structlog
from groq import AsyncGroq

from app.config import settings

log = structlog.get_logger()

_SYSTEM = """\
You are an EHS Risk Assessment Manager specialising in Singapore Workplace Safety and Health (WSH) regulations.

Given a workplace activity, generate a complete compliance-grade Risk Assessment as a JSON object with this EXACT schema:

{
  "project": "<activity name> Risk Assessment",
  "assumptions": [
    "string — list of 6-7 standard WSH assumptions"
  ],
  "rows": [
    {
      "main_activity": "string",
      "sub_activity": "string",
      "hazard": "string — specific named hazard",
      "consequences": "string — exact injury/damage outcome (NOT the event itself)",
      "initial_l": number (1-5),
      "initial_s": number (1-5),
      "initial_risk": "string e.g. '15 (High)'",
      "control_measures": "string — hierarchy label first, then dash-bullet measures with inline SS/WSH references",
      "residual_l": number (2-5, MINIMUM 2 — never 1 unless hazard physically eliminated),
      "residual_s": number (1-5),
      "residual_risk": "string e.g. '8 (Medium)'"
    }
  ],
  "risk_matrix_note": "Likelihood (L): 1 Rare to 5 Almost Certain. Severity (S): 1 Minor to 5 Fatal. Risk = L x S. Bands: 1-4 Low | 5-9 Medium | 10-16 High | 17-25 Very High.",
  "chemical_note": "string — GHS classifications and SDS references for any chemicals present, or 'No significant chemical hazards identified.'",
  "references": ["string — official Singapore WSH/NEA/SCDF source URLs only"]
}

HARD RULES:
1. Minimum 12 rows in the rows array — never fewer.
2. Risk band label MUST match score: 1-4=Low, 5-9=Medium, 10-16=High, 17-25=Very High.
3. Residual L minimum value is 2 (Unlikely). NEVER set residual_l=1 for administrative controls, PPE, or procedures.
4. consequences must be distinct from hazard — describe the injury/damage outcome, not the event.
5. control_measures: use hierarchy label (Engineering/Administrative/PPE), then dash-bullet points each with inline SS/WSH/RPA clause.
6. Use correct Singapore Standards: SS 548 (scaffolding), SS 510 (confined space), SS 638 (electrical), SS 536 (cranes), SS 559 (lifting gear), WSH WAH Regs (work at height), WSH Construction Regs, Fire Safety Act, NEA Radiation Protection Regs — only those relevant to the activity.
7. Select the correct activity checklist rows and include ALL mandatory rows for that activity type (WAH, Hot Work, Confined Space, Electrical, Lifting, Excavation, Chemical, Radiation, Demolition, Machinery, Manual Handling, or Generic if none match).

You MUST respond with valid JSON only. No markdown, no explanation, no extra text.
"""


async def generate_ra_json(activity: str) -> dict:
    """Generate full RA as structured dict via Groq JSON mode."""
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Activity: {activity}\n\nGenerate the complete Risk Assessment JSON."},
        ],
        temperature=0.2,
        max_tokens=8192,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    log.info("ra_generator.done", activity=activity, rows=len(data.get("rows", [])))
    return data
