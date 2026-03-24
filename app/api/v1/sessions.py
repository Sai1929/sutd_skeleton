import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.inspection import Activity, InspectionSession
from app.db.models.user import User
from app.dependencies import get_current_user, get_db, get_rec_engine
from app.schemas.recommendation import (
    ActivityOut,
    SessionStartRequest,
    SessionStartResponse,
    SessionStateOut,
    StepRequest,
    StepResponse,
)
from app.services.recommendation.chain import ChainedRecommender
from app.services.recommendation.session_state import SessionStateManager

router = APIRouter(prefix="/sessions", tags=["recommendations"])


def _make_recommender(db, rec_engine) -> ChainedRecommender:
    return ChainedRecommender(
        engine=rec_engine,
        state_manager=SessionStateManager(db),
        db=db,
    )


@router.get("/activities", response_model=list[ActivityOut])
async def list_activities(db: AsyncSession = Depends(get_db)) -> list[ActivityOut]:
    result = await db.execute(select(Activity).where(Activity.is_active.is_(True)))
    return [ActivityOut.model_validate(a) for a in result.scalars().all()]


@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    body: SessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rec_engine=Depends(get_rec_engine),
) -> SessionStartResponse:
    recommender = _make_recommender(db, rec_engine)
    data = await recommender.start_session(current_user.id, body.activity_id)
    return SessionStartResponse(**data)


@router.post("/{session_id}/step", response_model=StepResponse)
async def process_step(
    session_id: uuid.UUID,
    body: StepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rec_engine=Depends(get_rec_engine),
) -> StepResponse:
    await _assert_session_owner(session_id, current_user.id, db)
    recommender = _make_recommender(db, rec_engine)
    data = await recommender.process_step(session_id, body.step_number, body.selected_label)
    return StepResponse(**data)


@router.get("/{session_id}/state", response_model=SessionStateOut)
async def get_session_state(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rec_engine=Depends(get_rec_engine),
) -> SessionStateOut:
    await _assert_session_owner(session_id, current_user.id, db)
    recommender = _make_recommender(db, rec_engine)
    data = await recommender.get_state(session_id)
    return SessionStateOut(**data)


@router.delete("/{session_id}", status_code=204)
async def abandon_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await _assert_session_owner(session_id, current_user.id, db)
    session.status = "abandoned"
    await db.commit()
    mgr = SessionStateManager(db)
    await mgr.delete(session_id)


async def _assert_session_owner(
    session_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> InspectionSession:
    result = await db.execute(
        select(InspectionSession).where(InspectionSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Session not found")
    from app.core.exceptions import ForbiddenError
    if session.user_id != user_id:
        raise ForbiddenError("Not your session")
    return session
