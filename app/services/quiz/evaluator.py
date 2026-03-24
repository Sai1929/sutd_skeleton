"""
QuizEvaluator — scores MCQ instantly; uses GPT-4o mini for short-answer evaluation.
"""
from __future__ import annotations

import structlog
from openai import AsyncAzureOpenAI

from app.config import settings
from app.db.models.quiz import QuizAnswer, QuizAttempt, QuizQuestion
from app.schemas.quiz import AnswerItem, QuestionResult, QuizResult

log = structlog.get_logger()

SHORT_ANSWER_EVAL_PROMPT = """\
You are grading an EHS safety quiz.

Question: {question_text}
Model answer: {correct_answer}
Student answer: {student_answer}

Grade the student answer on a scale from 0.0 to 1.0.
Respond ONLY with a JSON object:
{{"score": <float 0-1>, "feedback": "<1 sentence feedback>"}}
"""


class QuizEvaluator:
    def __init__(self, client: AsyncAzureOpenAI) -> None:
        self._client = client

    async def evaluate(
        self,
        attempt: QuizAttempt,
        questions: list[QuizQuestion],
        answers: list[AnswerItem],
        db,
    ) -> QuizResult:
        import json

        q_map = {q.id: q for q in questions}
        answer_map = {a.question_id: a.answer for a in answers}

        per_question: list[QuestionResult] = []
        total_score = 0.0

        for q in questions:
            student_ans = answer_map.get(q.id, "")
            is_correct = None
            partial = 0.0
            llm_feedback = None

            if q.question_type == "mcq":
                # Normalise: accept "A", "A.", "A. text", "a"
                student_letter = student_ans.strip().upper()[:1]
                correct_letter = q.correct_answer.strip().upper()[:1]
                is_correct = student_letter == correct_letter
                partial = 1.0 if is_correct else 0.0

            elif q.question_type == "short_answer":
                # Call GPT-4o mini for grading
                prompt = SHORT_ANSWER_EVAL_PROMPT.format(
                    question_text=q.question_text,
                    correct_answer=q.correct_answer,
                    student_answer=student_ans,
                )
                resp = await self._client.chat.completions.create(
                    model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                grading = json.loads(resp.choices[0].message.content)
                partial = float(grading.get("score", 0.0))
                llm_feedback = grading.get("feedback")
                is_correct = partial >= 0.5

            total_score += partial

            answer_row = QuizAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                student_answer=student_ans,
                is_correct=is_correct,
                partial_score=partial,
                llm_feedback=llm_feedback,
            )
            db.add(answer_row)

            per_question.append(
                QuestionResult(
                    question_id=q.id,
                    is_correct=is_correct,
                    student_answer=student_ans,
                    correct_answer=q.correct_answer,
                    explanation=q.explanation,
                    llm_feedback=llm_feedback,
                )
            )

        n = len(questions)
        normalised_score = total_score / n if n > 0 else 0.0
        total_correct = sum(1 for r in per_question if r.is_correct)

        attempt.score = normalised_score
        attempt.submitted_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
        attempt.feedback = self._overall_feedback(normalised_score)

        await db.commit()

        return QuizResult(
            attempt_id=attempt.id,
            score=normalised_score,
            total_correct=total_correct,
            total_questions=n,
            feedback=attempt.feedback,
            per_question=per_question,
        )

    @staticmethod
    def _overall_feedback(score: float) -> str:
        if score >= 0.9:
            return "Excellent! You have a strong understanding of the EHS requirements."
        elif score >= 0.7:
            return "Good work. Review the flagged areas to strengthen your knowledge."
        elif score >= 0.5:
            return "Passing score. Please revisit the safety procedures for this activity."
        else:
            return "Below passing. Mandatory re-review of EHS guidelines is required."
