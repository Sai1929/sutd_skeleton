#!/usr/bin/env python3
"""
Load mock RA data from mock_ra_data.json into the database and ingest into RAG.

Creates:
  - Student users (RA team members)
  - InspectionSession + RecommendationStep x4 + InspectionSubmission per sub-activity
  - RAG document_chunks via IngestionPipeline

Usage:
    python scripts/load_mock_data.py
"""
import asyncio
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import AsyncAzureOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.db.models.inspection import (
    Activity,
    InspectionSession,
    InspectionSubmission,
    RecommendationStep,
)
from app.db.models.user import User
from app.services.rag.ingestion.pipeline import IngestionPipeline

DEFAULT_PASSWORD = "Test@1234"

# Map severity (1-5) x likelihood (1-5) → label_vocab string
def map_severity_likelihood(s: int, l: int) -> str:
    if s <= 2 and l <= 2:
        return "Low x Unlikely"
    if s <= 2 and l >= 3:
        return "Low x Likely"
    if s == 3 and l <= 2:
        return "Medium x Unlikely"
    if s == 3 and l >= 3:
        return "Medium x Likely"
    if s >= 4 and l <= 2:
        return "High x Unlikely"
    return "High x Likely"


def random_past_date(days_back: int = 180) -> datetime:
    delta = random.randint(1, days_back)
    return datetime.now(timezone.utc) - timedelta(days=delta)


async def get_or_create_activity(db: AsyncSession, name: str) -> int:
    result = await db.execute(select(Activity).where(Activity.name == name))
    activity = result.scalar_one_or_none()
    if activity is None:
        activity = Activity(name=name, is_active=True)
        db.add(activity)
        await db.flush()
        print(f"    + Activity created: {name}")
    return activity.id


async def get_or_create_user(db: AsyncSession, member: dict) -> User:
    result = await db.execute(select(User).where(User.student_id == member["student_id"]))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            student_id=member["student_id"],
            email=member["email"],
            password_hash=hash_password(DEFAULT_PASSWORD),
            full_name=member["full_name"],
            role="student",
            is_active=True,
        )
        db.add(user)
        await db.flush()
    return user


async def create_submission(
    db: AsyncSession,
    user: User,
    activity_id: int,
    activity_name: str,
    sub: dict,
    submitted_at: datetime,
) -> InspectionSubmission:
    severity_likelihood = map_severity_likelihood(sub["severity"], sub["likelihood"])
    hazard_type = sub["hazard_type"]
    moc_ppe = sub["risk_controls"]
    remarks = sub["possible_injury"]

    # Session
    session = InspectionSession(
        user_id=user.id,
        activity_id=activity_id,
        status="submitted",
        submitted_at=submitted_at,
    )
    db.add(session)
    await db.flush()

    # 4 recommendation steps
    steps = [
        (1, "hazard_type",          activity_name,   hazard_type),
        (2, "severity_likelihood",  hazard_type,     severity_likelihood),
        (3, "moc_ppe",              severity_likelihood, moc_ppe),
        (4, "remarks",              moc_ppe,         remarks),
    ]
    for step_number, step_name, model_input, selected_label in steps:
        db.add(RecommendationStep(
            session_id=session.id,
            step_number=step_number,
            step_name=step_name,
            model_input_text=model_input,
            ranked_options=[{"label": selected_label, "score": 1.0, "rank": 1}],
            selected_label=selected_label,
            confidence_score=1.0,
            responded_at=submitted_at,
        ))

    # Submission
    submission = InspectionSubmission(
        session_id=session.id,
        user_id=user.id,
        activity_name=activity_name,
        hazard_type=hazard_type,
        severity_likelihood=severity_likelihood,
        moc_ppe=moc_ppe,
        remarks=remarks,
        submitted_at=submitted_at,
    )
    db.add(submission)
    await db.flush()
    return submission


async def main() -> None:
    data_file = Path(__file__).parent / "mock_ra_data.json"
    with open(data_file) as f:
        ra_list = json.load(f)

    print(f"==> Loaded {len(ra_list)} RAs from {data_file.name}")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )

    total_users = 0
    total_submissions = 0
    total_chunks = 0

    async with SessionLocal() as db:
        pipeline = IngestionPipeline(client, db)

        for ra in ra_list:
            activity_name = ra["activity"]
            print(f"\n==> Processing {ra['ra_number']} — {activity_name}")

            activity_id = await get_or_create_activity(db, activity_name)

            # Create all team members
            users = []
            for member in ra["team"]:
                result = await db.execute(select(User).where(User.student_id == member["student_id"]))
                existing = result.scalar_one_or_none()
                if existing is None:
                    total_users += 1
                user = await get_or_create_user(db, member)
                users.append(user)

            await db.commit()

            # Each sub-activity → one submission per team member
            for sub in ra["sub_activities"]:
                for user in users:
                    submitted_at = random_past_date(180)
                    submission = await create_submission(
                        db, user, activity_id, activity_name, sub, submitted_at
                    )
                    await db.commit()

                    # RAG ingestion
                    try:
                        n = await pipeline.ingest_submission(submission)
                        total_chunks += n
                    except Exception as e:
                        print(f"    ! RAG ingest failed for submission {submission.id}: {e}")
                        n = 0

                    total_submissions += 1
                    print(
                        f"    [{ra['ra_number']}] {sub['name']} | "
                        f"{user.full_name} | {submission.hazard_type} | "
                        f"{submission.severity_likelihood} -> {n} chunks"
                    )

    await engine.dispose()
    print(f"\n==> Done.")
    print(f"    Users created : {total_users}")
    print(f"    Submissions   : {total_submissions}")
    print(f"    RAG chunks    : {total_chunks}")


if __name__ == "__main__":
    asyncio.run(main())
