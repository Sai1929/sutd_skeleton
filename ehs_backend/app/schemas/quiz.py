from typing import Literal
from pydantic import BaseModel


class QuizGenerateRequest(BaseModel):
    activity: str
    hazard_type: str
    severity_likelihood: str
    moc_ppe: str
    remarks: str = ""


class QuestionOut(BaseModel):
    question_number: int
    question_type: Literal["mcq", "descriptive", "scenario"]
    question_text: str
    options: list[str] | None        # MCQ only: ["A. ...", "B. ...", "C. ...", "D. ..."]
    correct_answer: str              # MCQ: "A"/"B"/"C"/"D" | descriptive/scenario: model answer text
    explanation: str | None


class QuizGenerateResponse(BaseModel):
    questions: list[QuestionOut]
