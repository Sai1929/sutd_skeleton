"""Hazard analysis from text or image input.

Identifies the hazard, assesses risk, and returns structured control measures
and mitigation activities per Singapore WSH hierarchy of controls.
"""
from __future__ import annotations

import json
import base64

import structlog
from groq import AsyncGroq

from app.config import settings
from app.schemas.hazard import ControlMeasure, HazardAnalysisResponse, MitigationActivity

log = structlog.get_logger()

_SYSTEM = """\
You are a senior EHS Risk Control Specialist with deep expertise in Singapore WSH regulations.

Given a text description or image of a workplace situation, hazard, or incident:

1. IDENTIFY the primary hazard (be specific — name the exact hazard, not a generic category)
2. ASSESS the risk using a 5×5 matrix (L×S where L=Likelihood 1-5, S=Severity 1-5)
   - Risk bands: 1-4 Low | 5-9 Medium | 10-16 High | 17-25 Very High
3. LIST potential consequences (specific injury/damage outcomes)
4. RECOMMEND control measures using the hierarchy of controls (Elimination → Substitution → Engineering → Administrative → PPE)
   - Each measure MUST cite the specific Singapore WSH regulation, SS standard, or Code of Practice inline
5. LIST mitigation activities — concrete actions, who is responsible, and priority (Immediate / Short-term / Ongoing)
6. LIST applicable Singapore regulations relevant to this specific hazard
7. DETERMINE residual risk after controls applied (Residual L minimum 2)

Return ONLY valid JSON matching this exact schema:
{
  "hazard_identified": "string — specific hazard name",
  "hazard_description": "string — 1-2 sentences describing what was observed and why it is dangerous",
  "risk_level": "string — e.g. 'High (L4 × S4 = 16)'",
  "potential_consequences": ["string", "string"],
  "control_measures": [
    {
      "hierarchy": "string — one of: Elimination | Substitution | Engineering | Administrative | PPE",
      "measures": ["string with inline WSH ref", "string with inline WSH ref"]
    }
  ],
  "mitigation_activities": [
    {
      "activity": "string — specific action to take",
      "responsible_party": "string — e.g. Supervisor, WSH Officer, Worker",
      "priority": "string — Immediate | Short-term | Ongoing"
    }
  ],
  "applicable_regulations": ["string — e.g. WSH (Work at Heights) Regulations", "SS 548 — Scaffolding"],
  "residual_risk": "string — e.g. 'Medium (L2 × S4 = 8)'"
}

HARD RULES:
- Be specific about the hazard — "Unguarded rotating shaft" not "Mechanical hazard"
- Consequences must be injury/damage outcomes, not event descriptions
- Every control measure must have an inline Singapore WSH/SS reference
- Residual L minimum is 2 — controls reduce likelihood but never eliminate it to 1 unless physical elimination/substitution occurred
- If image is provided, analyse what is visually present — do not fabricate what is not visible
- No markdown, no explanation outside the JSON object
"""


async def analyse_hazard(
    text: str | None,
    image_b64: str | None,
    image_mime: str = "image/jpeg",
) -> HazardAnalysisResponse:
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    # Build user message content — vision or text only
    if image_b64:
        content: list[dict] = []
        if text:
            content.append({"type": "text", "text": text})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
        })
    else:
        content = [{"type": "text", "text": text or "Analyse this workplace situation for hazards."}]

    log.info("hazard.analysing", has_image=bool(image_b64), has_text=bool(text))

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    log.info("hazard.done", hazard=data.get("hazard_identified"))

    return HazardAnalysisResponse(
        hazard_identified=data.get("hazard_identified", "Unknown hazard"),
        hazard_description=data.get("hazard_description", ""),
        risk_level=data.get("risk_level", ""),
        potential_consequences=data.get("potential_consequences", []),
        control_measures=[
            ControlMeasure(hierarchy=cm["hierarchy"], measures=cm["measures"])
            for cm in data.get("control_measures", [])
        ],
        mitigation_activities=[
            MitigationActivity(
                activity=ma["activity"],
                responsible_party=ma["responsible_party"],
                priority=ma["priority"],
            )
            for ma in data.get("mitigation_activities", [])
        ],
        applicable_regulations=data.get("applicable_regulations", []),
        residual_risk=data.get("residual_risk", ""),
    )
