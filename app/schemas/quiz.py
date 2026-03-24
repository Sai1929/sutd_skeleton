import uuid
from datetime import datetime

from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: int
    question_number: int
    question_type: str
    question_text: str
    options: list[str] | None

    model_config = {"from_attributes": True}


class QuizOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    total_questions: int
    status: str
    questions: list[QuestionOut]

    model_config = {"from_attributes": True}


class AnswerItem(BaseModel):
    question_id: int
    answer: str  # 'A'/'B'/'C'/'D' or free text


class AnswerSubmit(BaseModel):
    answers: list[AnswerItem]


class QuestionResult(BaseModel):
    question_id: int
    is_correct: bool | None
    student_answer: str
    correct_answer: str
    explanation: str | None
    llm_feedback: str | None


class QuizResult(BaseModel):
    attempt_id: uuid.UUID
    score: float
    total_correct: int
    total_questions: int
    feedback: str
    per_question: list[QuestionResult]
