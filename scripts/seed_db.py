#!/usr/bin/env python3
"""
Seed the database with activities, label vocab, and a test admin user.
Run once after alembic upgrade head.

Usage:
    python scripts/seed_db.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.db.models.inspection import Activity, LabelVocab
from app.db.models.user import User

ACTIVITIES = [
    "Welding",
    "Cleaning",
    "Chemical Handling",
    "Electrical Work",
    "Working at Height",
    "Machine Operation",
    "Material Handling",
    "Hot Work",
]

# Sample label vocab — replace with actual client dataset labels
LABEL_VOCAB = {
    "hazard_type": [
        "Arc Flash",
        "Chemical Burn",
        "Electric Shock",
        "Fall from Height",
        "Fire/Explosion",
        "Crush Injury",
        "Noise",
        "UV Radiation",
        "Fume Inhalation",
        "Slip/Trip",
    ],
    "severity_likelihood": [
        "High x Likely",
        "High x Unlikely",
        "Medium x Likely",
        "Medium x Unlikely",
        "Low x Likely",
        "Low x Unlikely",
    ],
    "moc_ppe": [
        "Full Face Shield + FR Jacket",
        "Chemical Resistant Gloves + Apron",
        "Safety Harness + Lanyard",
        "Insulated Gloves + Lock-Out Tag-Out",
        "Respiratory Mask + Goggles",
        "Hard Hat + Safety Boots",
        "Hearing Protection + Goggles",
        "Fire Extinguisher + Hot Work Permit",
    ],
    "remarks": [
        "Ensure area is barricaded and signage posted",
        "Check SDS before starting work",
        "Conduct toolbox talk before operation",
        "Verify all PPE is in serviceable condition",
        "Obtain permit-to-work before proceeding",
        "Ensure buddy system in place",
        "No lone worker allowed",
    ],
}

ADMIN_USER = {
    "student_id": "ADMIN001",
    "email": "admin@ehs.local",
    "password": "Admin@123",  # Change in production
    "role": "admin",
    "full_name": "System Administrator",
}


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        from sqlalchemy import select

        # Seed activities
        print("==> Seeding activities…")
        for name in ACTIVITIES:
            result = await db.execute(select(Activity).where(Activity.name == name))
            if result.scalar_one_or_none() is None:
                db.add(Activity(name=name))
        await db.commit()
        print(f"    {len(ACTIVITIES)} activities seeded.")

        # Seed label vocab
        print("==> Seeding label vocab…")
        count = 0
        for step, labels in LABEL_VOCAB.items():
            for idx, label_value in enumerate(labels):
                result = await db.execute(
                    select(LabelVocab).where(
                        LabelVocab.step == step,
                        LabelVocab.label_value == label_value,
                    )
                )
                if result.scalar_one_or_none() is None:
                    db.add(LabelVocab(step=step, label_value=label_value, label_index=idx))
                    count += 1
        await db.commit()
        print(f"    {count} label vocab entries seeded.")

        # Seed admin user
        print("==> Seeding admin user…")
        result = await db.execute(
            select(User).where(User.student_id == ADMIN_USER["student_id"])
        )
        if result.scalar_one_or_none() is None:
            db.add(
                User(
                    student_id=ADMIN_USER["student_id"],
                    email=ADMIN_USER["email"],
                    password_hash=hash_password(ADMIN_USER["password"]),
                    role=ADMIN_USER["role"],
                    full_name=ADMIN_USER["full_name"],
                )
            )
            await db.commit()
            print(f"    Admin user created: {ADMIN_USER['student_id']}")
        else:
            print("    Admin user already exists, skipping.")

    await engine.dispose()
    print("==> Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
