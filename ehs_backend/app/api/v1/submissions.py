import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.db.models.inspection import InspectionSession, InspectionSubmission, RecommendationStep
from app.db.models.quiz import Quiz
from app.dependencies import get_azure_llm, get_db
from app.schemas.submission import SubmissionCreate, SubmissionOut

log = structlog.get_logger()
router = APIRouter(prefix="/submissions", tags=["submissions"])


async def _background_quiz_and_ingest(
    submission_id: uuid.UUID,
    session_id: uuid.UUID,
    db_url: str,
    azure_llm,
) -> None:
    """
    Run quiz generation and RAG ingestion in the background.
    Uses a fresh DB session to avoid sharing the request session.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(InspectionSubmission).where(InspectionSubmission.id == submission_id)
            )
            submission = result.scalar_one_or_none()
            if submission is None:
                log.error("background.submission_not_found", submission_id=str(submission_id))
                return

            from app.services.quiz.generator import QuizGenerator
            from openai import AsyncAzureOpenAI
            from app.config import settings

            client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )

            try:
                generator = QuizGenerator(client)
                await generator.generate(submission, session_id, db)
                log.info("background.quiz_generated", submission_id=str(submission_id))
            except Exception as e:
                log.error("background.quiz_failed", submission_id=str(submission_id), error=str(e))

    except Exception as e:
        log.error("background.task_failed", submission_id=str(submission_id), error=str(e))
    finally:
        await engine.dispose()


@router.post("", response_model=SubmissionOut, status_code=201)
async def create_submission(
    body: SubmissionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    azure_llm=Depends(get_azure_llm),
) -> SubmissionOut:
    # Validate session exists and is ready
    result = await db.execute(
        select(InspectionSession).where(InspectionSession.id == body.session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Session not found")
    if session.status not in ("ready_to_submit", "in_progress"):
        raise BadRequestError(f"Session status '{session.status}' cannot be submitted")

    # Check no duplicate submission
    dup = await db.execute(
        select(InspectionSubmission).where(InspectionSubmission.session_id == body.session_id)
    )
    if dup.scalar_one_or_none():
        raise BadRequestError("Session already submitted")

    # Collect completed steps
    steps_result = await db.execute(
        select(RecommendationStep)
        .where(RecommendationStep.session_id == body.session_id)
        .order_by(RecommendationStep.step_number)
    )
    steps = steps_result.scalars().all()

    selections = {s.step_name: s.selected_label for s in steps if s.selected_label}

    # Fetch activity name
    from app.db.models.inspection import Activity
    act_result = await db.execute(select(Activity).where(Activity.id == session.activity_id))
    activity = act_result.scalar_one()

    submission = InspectionSubmission(
        session_id=body.session_id,
        user_id=session.user_id or uuid.uuid4(),
        activity_name=activity.name,
        hazard_type=selections.get("hazard_type"),
        severity_likelihood=selections.get("severity_likelihood"),
        moc_ppe=selections.get("moc_ppe"),
        remarks=selections.get("remarks"),
    )
    db.add(submission)
    session.status = "submitted"
    await db.commit()
    await db.refresh(submission)

    # Background: quiz generation
    from app.config import settings
    background_tasks.add_task(
        _background_quiz_and_ingest,
        submission.id,
        body.session_id,
        settings.DATABASE_URL,
        azure_llm,
    )

    # Resolve quiz_id if already exists (unlikely, but safe)
    quiz_result = await db.execute(
        select(Quiz).where(Quiz.session_id == body.session_id)
    )
    quiz = quiz_result.scalar_one_or_none()

    out = SubmissionOut.model_validate(submission)
    out.quiz_id = quiz.id if quiz else None
    return out


@router.get("", response_model=list[SubmissionOut])
async def list_submissions(
    db: AsyncSession = Depends(get_db),
) -> list[SubmissionOut]:
    result = await db.execute(
        select(InspectionSubmission)
        .order_by(InspectionSubmission.submitted_at.desc())
    )
    submissions = result.scalars().all()

    out = []
    for sub in submissions:
        quiz_result = await db.execute(select(Quiz).where(Quiz.session_id == sub.session_id))
        quiz = quiz_result.scalar_one_or_none()
        item = SubmissionOut.model_validate(sub)
        item.quiz_id = quiz.id if quiz else None
        out.append(item)
    return out


@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SubmissionOut:
    result = await db.execute(
        select(InspectionSubmission).where(InspectionSubmission.id == submission_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        raise NotFoundError("Submission not found")

    quiz_result = await db.execute(select(Quiz).where(Quiz.session_id == sub.session_id))
    quiz = quiz_result.scalar_one_or_none()

    out = SubmissionOut.model_validate(sub)
    out.quiz_id = quiz.id if quiz else None
    return out
