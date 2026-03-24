"""
IngestionPipeline — serialize → chunk → embed → upsert to document_chunks.
Triggered as a background task after submission and quiz answer save.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from openai import AsyncAzureOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.inspection import InspectionSubmission
from app.db.models.rag import DocumentChunk
from app.services.rag.ingestion.chunker import SemanticChunker
from app.services.rag.ingestion.embedder import AzureEmbedder

log = structlog.get_logger()


def _serialize_submission(sub: InspectionSubmission) -> str:
    return (
        f"EHS Inspection Record. "
        f"Activity: {sub.activity_name}. "
        f"Identified Hazard Type: {sub.hazard_type or 'Not specified'}. "
        f"Risk Assessment (Severity x Likelihood): {sub.severity_likelihood or 'Not specified'}. "
        f"Control Measures (MOC/PPE): {sub.moc_ppe or 'Not specified'}. "
        f"Remarks: {sub.remarks or 'None'}. "
        f"Submitted at: {sub.submitted_at.strftime('%Y-%m-%d') if sub.submitted_at else 'Unknown'}."
    )


def _serialize_quiz_attempt(
    attempt,
    questions: list,
    answers: list,
) -> str:
    lines = [
        "EHS Quiz Record. ",
        f"Score: {(attempt.score or 0) * 100:.0f}%. ",
    ]
    answer_map = {a.question_id: a.student_answer for a in answers}
    for q in questions:
        student_ans = answer_map.get(q.id, "No answer")
        lines.append(
            f"Q{q.question_number}: {q.question_text} "
            f"Student answer: {student_ans}. "
            f"Correct answer: {q.correct_answer}. "
            f"Explanation: {q.explanation or 'N/A'}. "
        )
    return "".join(lines)


class IngestionPipeline:
    def __init__(self, azure_client: AsyncAzureOpenAI, db: AsyncSession) -> None:
        self._embedder = AzureEmbedder(azure_client)
        self._chunker = SemanticChunker(
            target_tokens=settings.CHUNK_TARGET_TOKENS,
            overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        )
        self._db = db

    async def ingest_submission(self, submission: InspectionSubmission) -> int:
        doc_text = _serialize_submission(submission)
        metadata = {
            "activity_name": submission.activity_name,
            "hazard_type": submission.hazard_type,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "user_id": str(submission.user_id),
        }
        chunks = self._chunker.chunk(doc_text, metadata)
        return await self._upsert_chunks(
            chunks,
            source_type="inspection_submission",
            source_id=submission.id,
            submission=submission,
        )

    async def ingest_quiz_attempt(self, attempt, questions: list, answers: list) -> int:
        doc_text = _serialize_quiz_attempt(attempt, questions, answers)
        chunks = self._chunker.chunk(doc_text, {})
        return await self._upsert_chunks(
            chunks,
            source_type="quiz_qa",
            source_id=attempt.id,
        )

    async def _upsert_chunks(
        self,
        chunks,
        source_type: str,
        source_id: uuid.UUID,
        submission: InspectionSubmission | None = None,
    ) -> int:
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        embeddings = await self._embedder.embed_batch(texts)

        rows = []
        for chunk, embedding in zip(chunks, embeddings):
            meta = chunk.metadata

            row = DocumentChunk(
                source_type=source_type,
                source_id=source_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.text,
                token_count=chunk.token_count,
                activity_name=meta.get("activity_name") or (
                    submission.activity_name if submission else None
                ),
                hazard_type=meta.get("hazard_type") or (
                    submission.hazard_type if submission else None
                ),
                submitted_at=(
                    submission.submitted_at if submission
                    else datetime.now(timezone.utc)
                ),
                user_id=uuid.UUID(meta["user_id"]) if meta.get("user_id") else (
                    submission.user_id if submission else None
                ),
                embedding=embedding.tolist(),
            )
            rows.append(row)
            self._db.add(row)

        await self._db.commit()
        log.info(
            "rag.ingested",
            source_type=source_type,
            source_id=str(source_id),
            num_chunks=len(rows),
        )
        return len(rows)
