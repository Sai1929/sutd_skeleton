"""
PostgreSQL-backed session state manager for the chained recommendation flow.
State is stored as JSONB in inspection_sessions.state_json.
Stale sessions (updated_at < NOW() - interval) are cleaned by a background task.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inspection import InspectionSession


@dataclass
class SessionState:
    session_id: str
    user_id: str
    activity_id: int
    activity_name: str
    current_step: int = 1  # 1-indexed, 1..4
    selections: dict[str, str] = field(default_factory=dict)  # step_name -> chosen label
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionStateManager:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, state: SessionState) -> None:
        await self._db.execute(
            update(InspectionSession)
            .where(InspectionSession.id == _as_uuid(state.session_id))
            .values(state_json=asdict(state))
        )
        await self._db.commit()

    async def get(self, session_id: str | uuid.UUID) -> SessionState | None:
        result = await self._db.execute(
            select(InspectionSession.state_json)
            .where(InspectionSession.id == _as_uuid(session_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return SessionState(**row)

    async def update(self, state: SessionState) -> None:
        await self._db.execute(
            update(InspectionSession)
            .where(InspectionSession.id == _as_uuid(state.session_id))
            .values(state_json=asdict(state))
        )
        await self._db.commit()

    async def delete(self, session_id: str | uuid.UUID) -> None:
        await self._db.execute(
            update(InspectionSession)
            .where(InspectionSession.id == _as_uuid(session_id))
            .values(state_json=None)
        )
        await self._db.commit()

    async def exists(self, session_id: str | uuid.UUID) -> bool:
        result = await self._db.execute(
            select(InspectionSession.state_json)
            .where(InspectionSession.id == _as_uuid(session_id))
        )
        row = result.scalar_one_or_none()
        return row is not None


def _as_uuid(session_id: str | uuid.UUID) -> uuid.UUID:
    return session_id if isinstance(session_id, uuid.UUID) else uuid.UUID(str(session_id))
