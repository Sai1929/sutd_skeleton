"""
ChainedRecommender — orchestrates the 4-step popup flow.
Manages DB persistence, PostgreSQL session state, and frequency-ranked inference.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.db.models.inspection import Activity, InspectionSession, RecommendationStep
from app.services.recommendation.engine import RankedOption, RecommendationEngine, STEP_NAMES
from app.services.recommendation.session_state import SessionState, SessionStateManager

log = structlog.get_logger()

# (step_number 1-indexed, step_name)
STEPS: list[tuple[int, str]] = [(i + 1, name) for i, name in enumerate(STEP_NAMES)]
TOTAL_STEPS = len(STEPS)


class ChainedRecommender:
    def __init__(
        self,
        engine: RecommendationEngine,
        state_manager: SessionStateManager,
        db: AsyncSession,
    ) -> None:
        self._engine = engine
        self._state = state_manager
        self._db = db

    # ── Public API ────────────────────────────────────────────────

    async def start_session(
        self, user_id: uuid.UUID, activity_id: int
    ) -> dict:
        """Create DB session + init PostgreSQL state + run Step 1 frequency ranking."""
        activity = await self._get_activity(activity_id)

        session = InspectionSession(
            user_id=user_id,
            activity_id=activity_id,
            status="in_progress",
        )
        self._db.add(session)
        await self._db.flush()  # get session.id without committing

        state = SessionState(
            session_id=str(session.id),
            user_id=str(user_id),
            activity_id=activity_id,
            activity_name=activity.name,
            current_step=1,
        )
        await self._state.create(state)

        # Run Step 1 frequency ranking
        step_number, step_name = STEPS[0]
        options = await self._engine.get_ranked_options(
            db=self._db,
            activity=activity.name,
            selections={},
            step_name=step_name,
        )

        # Persist the step row (no selection yet)
        step_row = RecommendationStep(
            session_id=session.id,
            step_number=step_number,
            step_name=step_name,
            model_input_text=activity.name,
            ranked_options=[{"label": o.label, "score": o.score, "rank": o.rank} for o in options],
        )
        self._db.add(step_row)
        await self._db.commit()

        log.info("session.started", session_id=str(session.id), activity=activity.name)

        return {
            "session_id": session.id,
            "activity_name": activity.name,
            "current_step": step_number,
            "step_name": step_name,
            "options": [{"label": o.label, "score": o.score, "rank": o.rank} for o in options],
            "total_steps": TOTAL_STEPS,
        }

    async def process_step(
        self,
        session_id: uuid.UUID,
        step_number: int,
        selected_label: str,
    ) -> dict:
        """Submit selection for current step; infer options for next step."""
        state = await self._state.get(session_id)
        if state is None:
            # Reconstruct from DB (state_json missing or expired)
            state = await self._reconstruct_state(session_id)

        if state.current_step != step_number:
            raise BadRequestError(
                f"Expected step {state.current_step}, got {step_number}"
            )

        _, step_name = STEPS[step_number - 1]

        # Persist selection on existing step row
        result = await self._db.execute(
            select(RecommendationStep).where(
                RecommendationStep.session_id == session_id,
                RecommendationStep.step_number == step_number,
            )
        )
        step_row = result.scalar_one_or_none()
        if step_row is None:
            raise NotFoundError(f"Step {step_number} not found for session")

        step_row.selected_label = selected_label
        step_row.responded_at = datetime.now(timezone.utc)

        # Update Redis state
        state.selections[step_name] = selected_label

        is_final = step_number == TOTAL_STEPS

        if is_final:
            state.current_step = TOTAL_STEPS + 1  # mark done
            await self._state.update(state)

            session_result = await self._db.execute(
                select(InspectionSession).where(InspectionSession.id == session_id)
            )
            session = session_result.scalar_one()
            session.status = "ready_to_submit"

            await self._db.commit()
            log.info("session.completed", session_id=str(session_id))

            return {
                "session_id": session_id,
                "completed_step": step_number,
                "next_step": None,
                "next_step_name": None,
                "options": None,
                "is_final": True,
                "summary": self._build_summary(state),
            }

        # Not final — compute next step options
        next_step_number, next_step_name = STEPS[step_number]
        next_options = await self._engine.get_ranked_options(
            db=self._db,
            activity=state.activity_name,
            selections=state.selections,
            step_name=next_step_name,
        )

        # Persist next step placeholder row
        sel_str = " | ".join(f"{k}={v}" for k, v in state.selections.items())
        input_text = f"{state.activity_name} | {sel_str}" if sel_str else state.activity_name
        next_step_row = RecommendationStep(
            session_id=session_id,
            step_number=next_step_number,
            step_name=next_step_name,
            model_input_text=input_text,
            ranked_options=[
                {"label": o.label, "score": o.score, "rank": o.rank} for o in next_options
            ],
        )
        self._db.add(next_step_row)

        state.current_step = next_step_number
        await self._state.update(state)
        await self._db.commit()

        return {
            "session_id": session_id,
            "completed_step": step_number,
            "next_step": next_step_number,
            "next_step_name": next_step_name,
            "options": [{"label": o.label, "score": o.score, "rank": o.rank} for o in next_options],
            "is_final": False,
            "summary": None,
        }

    async def get_state(self, session_id: uuid.UUID) -> dict:
        state = await self._state.get(session_id)
        if state is None:
            state = await self._reconstruct_state(session_id)

        current_step_name = (
            STEP_NAMES[state.current_step - 1]
            if state.current_step <= TOTAL_STEPS
            else None
        )

        # Get current step's options from DB
        options = []
        if current_step_name:
            result = await self._db.execute(
                select(RecommendationStep).where(
                    RecommendationStep.session_id == session_id,
                    RecommendationStep.step_number == state.current_step,
                )
            )
            row = result.scalar_one_or_none()
            if row:
                options = [
                    RankedOption(**opt) for opt in row.ranked_options
                ]

        return {
            "session_id": session_id,
            "status": "in_progress" if state.current_step <= TOTAL_STEPS else "completed",
            "current_step": state.current_step,
            "selections": state.selections,
            "options_for_current_step": options,
        }

    # ── Helpers ───────────────────────────────────────────────────

    async def _get_activity(self, activity_id: int) -> Activity:
        result = await self._db.execute(
            select(Activity).where(Activity.id == activity_id, Activity.is_active.is_(True))
        )
        activity = result.scalar_one_or_none()
        if activity is None:
            raise NotFoundError(f"Activity {activity_id} not found")
        return activity

    async def _reconstruct_state(self, session_id: uuid.UUID) -> SessionState:
        """Rebuild Redis state from DB rows after TTL expiry."""
        result = await self._db.execute(
            select(InspectionSession).where(InspectionSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise NotFoundError("Session not found")

        steps_result = await self._db.execute(
            select(RecommendationStep)
            .where(RecommendationStep.session_id == session_id)
            .order_by(RecommendationStep.step_number)
        )
        steps = steps_result.scalars().all()

        selections = {
            step.step_name: step.selected_label
            for step in steps
            if step.selected_label is not None
        }
        current_step = len(selections) + 1

        activity_result = await self._db.execute(
            select(Activity).where(Activity.id == session.activity_id)
        )
        activity = activity_result.scalar_one()

        state = SessionState(
            session_id=str(session_id),
            user_id=str(session.user_id),
            activity_id=session.activity_id,
            activity_name=activity.name,
            current_step=current_step,
            selections=selections,
        )
        await self._state.create(state)
        return state

    def _build_summary(self, state: SessionState) -> dict:
        return {
            "session_id": state.session_id,
            "activity_name": state.activity_name,
            "hazard_type": state.selections.get("hazard_type"),
            "severity_likelihood": state.selections.get("severity_likelihood"),
            "moc_ppe": state.selections.get("moc_ppe"),
            "remarks": state.selections.get("remarks"),
        }
