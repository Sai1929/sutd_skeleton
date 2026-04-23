import uuid
from datetime import datetime

from pydantic import BaseModel


class ActivityOut(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class RankedOption(BaseModel):
    label: str
    score: float
    rank: int


class SessionStartRequest(BaseModel):
    activity_id: int


class SessionStartResponse(BaseModel):
    session_id: uuid.UUID
    activity_name: str
    current_step: int
    step_name: str
    options: list[RankedOption]
    total_steps: int = 4


class StepRequest(BaseModel):
    step_number: int
    selected_label: str


class InspectionSummary(BaseModel):
    session_id: uuid.UUID | str
    activity_name: str
    hazard_type: str | None
    severity_likelihood: str | None
    moc_ppe: str | None
    remarks: str | None


class StepResponse(BaseModel):
    session_id: uuid.UUID
    completed_step: int
    next_step: int | None
    next_step_name: str | None
    options: list[RankedOption] | None
    is_final: bool
    summary: InspectionSummary | None


class SessionStateOut(BaseModel):
    session_id: uuid.UUID
    status: str
    current_step: int
    selections: dict[str, str]
    options_for_current_step: list[RankedOption]
