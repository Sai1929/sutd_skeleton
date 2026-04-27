from pydantic import BaseModel


class ControlMeasure(BaseModel):
    hierarchy: str        # "Elimination" | "Substitution" | "Engineering" | "Administrative" | "PPE"
    measures: list[str]   # each item is one bullet with inline WSH ref


class MitigationActivity(BaseModel):
    activity: str
    responsible_party: str
    priority: str         # "Immediate" | "Short-term" | "Ongoing"


class HazardAnalysisResponse(BaseModel):
    hazard_identified: str
    hazard_description: str
    risk_level: str                        # e.g. "High (L4 × S4 = 16)"
    potential_consequences: list[str]
    control_measures: list[ControlMeasure]
    mitigation_activities: list[MitigationActivity]
    applicable_regulations: list[str]
    residual_risk: str                     # e.g. "Medium (L2 × S4 = 8)"
