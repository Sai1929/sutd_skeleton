from pydantic import BaseModel


class RankedOption(BaseModel):
    label: str
    score: float
    rank: int


class RecommendRequest(BaseModel):
    activity: str
    selections: dict[str, str] = {}  # e.g. {"hazard_type": "Arc Flash"}


class RecommendResponse(BaseModel):
    activity: str
    selections: dict[str, str]
    predictions: dict[str, list[RankedOption]]  # step_name -> ranked options
