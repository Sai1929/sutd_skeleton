import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.db.models.quiz import Quiz, QuizAnswer, QuizAttempt, QuizQuestion
from app.db.models.user import User
from app.dependencies import get_current_user, get_db
from app.schemas.quiz import AnswerSubmit, QuestionAnswer, QuestionOut, QuizOut, QuizSubmissionOut
from app.services.quiz.evaluator import QuizEvaluator

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/{quiz_id}", response_model=QuizOut)
async def get_quiz(
    quiz_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizOut:
    quiz = await _get_quiz(quiz_id, db)

    questions_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.question_number)
    )
    questions = questions_result.scalars().all()

    return QuizOut(
        id=quiz.id,
        session_id=quiz.session_id,
        total_questions=quiz.total_questions,
        status=quiz.status,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


@router.post("/{quiz_id}/attempt", status_code=201)
async def start_attempt(
    quiz_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    quiz = await _get_quiz(quiz_id, db)

    attempt = QuizAttempt(quiz_id=quiz_id, user_id=current_user.id)
    db.add(attempt)
    quiz.status = "attempted"
    await db.commit()
    await db.refresh(attempt)

    return {"attempt_id": attempt.id, "quiz_id": quiz_id}


@router.post("/{quiz_id}/attempt/{attempt_id}/submit", response_model=QuizSubmissionOut)
async def submit_attempt(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    body: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizSubmissionOut:
    attempt_result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.quiz_id == quiz_id,
        )
    )
    attempt = attempt_result.scalar_one_or_none()
    if attempt is None:
        raise NotFoundError("Attempt not found")
    if attempt.user_id != current_user.id:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Not your attempt")
    if attempt.submitted_at is not None:
        raise BadRequestError("Attempt already submitted")

    questions_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.question_number)
    )
    questions = questions_result.scalars().all()

    evaluator = QuizEvaluator()
    result = await evaluator.store(attempt, questions, body.answers, db)

    # Ingest Q&A into RAG for chatbot context
    try:
        from app.config import settings
        from openai import AsyncAzureOpenAI
        from app.services.rag.ingestion.pipeline import IngestionPipeline
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        pipeline = IngestionPipeline(client, db)
        await pipeline.ingest_quiz_attempt(attempt, questions, body.answers)
    except Exception as exc:
        import structlog
        structlog.get_logger().warning("rag_ingest_quiz_failed", error=str(exc))

    return result


@router.get("/{quiz_id}/attempt/{attempt_id}/result", response_model=QuizSubmissionOut)
async def get_result(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizSubmissionOut:
    """
    Returns the full Q&A record for an attempt.
    Intended for admin review: shows each question, the student's answer,
    the reference answer, and the admin note from the LLM.
    """
    attempt_result = await db.execute(
        select(QuizAttempt).where(QuizAttempt.id == attempt_id)
    )
    attempt = attempt_result.scalar_one_or_none()
    if attempt is None:
        raise NotFoundError("Attempt not found")
    if attempt.submitted_at is None:
        raise BadRequestError("Attempt not yet submitted")

    questions_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.question_number)
    )
    questions = questions_result.scalars().all()
    q_map = {q.id: q for q in questions}

    answers_result = await db.execute(
        select(QuizAnswer).where(QuizAnswer.attempt_id == attempt_id)
    )
    answers = answers_result.scalars().all()

    qa_list = [
        QuestionAnswer(
            question_id=a.question_id,
            question_number=q_map[a.question_id].question_number,
            question_text=q_map[a.question_id].question_text,
            options=q_map[a.question_id].options,
            student_answer=a.student_answer,
            reference_answer=q_map[a.question_id].correct_answer,
            admin_note=q_map[a.question_id].explanation,
        )
        for a in answers
    ]

    return QuizSubmissionOut(
        attempt_id=attempt.id,
        quiz_id=quiz_id,
        submitted_at=attempt.submitted_at,
        answers=qa_list,
    )


async def _get_quiz(quiz_id: uuid.UUID, db: AsyncSession) -> Quiz:
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise NotFoundError("Quiz not found")
    return quiz
