#!/usr/bin/env python3
"""
Bulk-ingest existing inspection_submissions into the RAG vector store.
Run this once after deploying to populate document_chunks for historical records.

Usage:
    python scripts/ingest_historical_data.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import AsyncAzureOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models.inspection import InspectionSubmission
from app.services.rag.ingestion.pipeline import IngestionPipeline


async def main() -> None:
    print("==> Connecting to database…")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )

    async with SessionLocal() as db:
        result = await db.execute(select(InspectionSubmission))
        submissions = result.scalars().all()
        print(f"==> Found {len(submissions)} submissions to ingest.")

        pipeline = IngestionPipeline(client, db)
        total = 0
        for i, sub in enumerate(submissions, 1):
            n = await pipeline.ingest_submission(sub)
            total += n
            print(f"    [{i}/{len(submissions)}] submission={sub.id} → {n} chunks")

    await engine.dispose()
    print(f"==> Done. Total chunks ingested: {total}")


if __name__ == "__main__":
    asyncio.run(main())
