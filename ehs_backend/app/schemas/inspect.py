from pydantic import BaseModel


class RecommendRequest(BaseModel):
    activity: str


class RARow(BaseModel):
    main_activity: str
    sub_activity: str
    hazard: str
    consequences: str
    initial_l: int
    initial_s: int
    initial_risk: str
    control_measures: str
    residual_l: int
    residual_s: int
    residual_risk: str


class RecommendResponse(BaseModel):
    activity: str
    from_db: bool
    project: str
    assumptions: list[str]
    rows: list[RARow]
    full_ra: dict | None = None
