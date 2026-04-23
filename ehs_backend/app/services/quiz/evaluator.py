"""
QuizEvaluator — stores student answers to the operational questionnaire.
No scoring or grading: the questionnaire is a data-capture tool for admins.
"""
from __future__ import annotations

import datetime

import structlog

from app.db.models.quiz import QuizAnswer, QuizAttempt, QuizQuestion
from app.schemas.quiz import AnswerItem, QuestionAnswer, QuizSubmissionOut

log = structlog.get_logger()


class QuizEvaluator:
    async def store(
        self,
        attempt: QuizAttempt,
        questions: list[QuizQuestion],
        answers: list[AnswerItem],
        db,
    ) -> QuizSubmissionOut:
        """Persist student answers; return the full Q&A record for admin review."""
        answer_map = {a.question_id: a.answer for a in answers}

        stored: list[QuestionAnswer] = []

        for q in questions:
            student_ans = answer_map.get(q.id, "")

            db.add(QuizAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                student_answer=student_ans,
                is_correct=None,
                partial_score=None,
                llm_feedback=None,
            ))

            stored.append(QuestionAnswer(
                question_id=q.id,
                question_number=q.question_number,
                question_text=q.question_text,
                options=q.options,
                student_answer=student_ans,
                reference_answer=q.correct_answer,
                admin_note=q.explanation,
            ))

        now = datetime.datetime.now(datetime.timezone.utc)
        attempt.submitted_at = now
        attempt.score = None
        attempt.feedback = None

        await db.commit()

        log.info("quiz.readiness_stored", attempt_id=str(attempt.id), num_answers=len(stored))

        return QuizSubmissionOut(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            submitted_at=now,
            answers=stored,
        )
