from pydantic import BaseModel


class QuizGenerateRequest(BaseModel):
    activity: str
    hazard_type: str
    severity_likelihood: str
    moc_ppe: str
    remarks: str = ""


class QuestionOut(BaseModel):
    question_number: int
    question_text: str
    options: list[str] | None
    correct_answer: str
    explanation: str | None


class QuizGenerateResponse(BaseModel):
    questions: list[QuestionOut]
