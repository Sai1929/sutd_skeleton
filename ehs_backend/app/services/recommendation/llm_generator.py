"""Generate inspection fields from LLM when DB has no match."""
import json
import re

import structlog
from groq import AsyncGroq

from app.config import settings

log = structlog.get_logger()

_SYSTEM = """\
You are an EHS (Environment, Health & Safety) expert specialising in Singapore Workplace Safety and Health (WSH) regulations.
Given a workplace activity, return a JSON object with these exact keys:
- hazard_types: array of 3 to 4 SPECIFIC named hazards (not broad categories). \
Examples of good specific hazards: "Fall from Height", "Arc Flash / UV Radiation", "Fume Inhalation", \
"Fire and Explosion", "Electric Shock", "Crush Injury", "Heat Stress", "Noise-Induced Hearing Loss", \
"Chemical Burn", "Oxygen Deficiency", "Manual Handling Injury", "Struck by Falling Object". \
Do NOT return generic categories like "Physical", "Chemical", "Biological", "Thermal".
- severity_likelihood: one concise label chosen from: \
"High x Likely", "High x Unlikely", "Medium x Likely", "Medium x Unlikely", "Low x Likely", "Low x Unlikely". \
Base this on the most severe hazard in the list — not all hazards are High x Likely.
- moc_ppe: the primary control measure and required PPE as a single string
- remarks: a single actionable safety remark

You MUST respond with a valid JSON object only. No explanation, no markdown, no extra text.
"""

_USER_TMPL = 'Activity: "{activity}"\n\nGenerate the EHS inspection fields.'


async def generate_recommendation(activity: str) -> dict:
    """Call Groq and return parsed dict with 4 fields."""
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    prompt = _USER_TMPL.format(activity=activity)

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or ""
    log.info("llm_generator.raw", activity=activity, raw=raw[:200])

    # Fallback strip in case model wraps in fences despite JSON mode
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    data = json.loads(cleaned)

    hazard_types = data.get("hazard_types", [])
    if isinstance(hazard_types, str):
        hazard_types = [hazard_types]
    hazard_types = [str(h) for h in hazard_types[:4]]

    return {
        "hazard_types": hazard_types,
        "severity_likelihood": str(data.get("severity_likelihood", "")),
        "moc_ppe": str(data.get("moc_ppe", "")),
        "remarks": str(data.get("remarks", "")),
    }
