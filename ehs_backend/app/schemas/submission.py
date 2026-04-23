import uuid
from datetime import datetime

from pydantic import BaseModel


class SubmissionCreate(BaseModel):
    session_id: uuid.UUID


class SubmissionOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    activity_name: str
    hazard_type: str | None
    severity_likelihood: str | None
    moc_ppe: str | None
    remarks: str | None
    submitted_at: datetime
    quiz_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
