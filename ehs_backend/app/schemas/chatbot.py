import uuid
from datetime import date, datetime

from pydantic import BaseModel


class QueryFilters(BaseModel):
    activity_name: str | None = None
    hazard_type: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class ChatQuery(BaseModel):
    query: str
    conversation_id: str | None = None
    filters: QueryFilters | None = None


class SourceCitation(BaseModel):
    chunk_id: int
    source_type: str
    source_id: uuid.UUID
    activity_name: str | None
    chunk_text_preview: str
    relevance_score: float


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    query_type: str
    sources: list[SourceCitation]
    retrieved_chunks_count: int
    reranked_chunks_count: int
    latency_ms: float


class ChatTurn(BaseModel):
    role: str  # 'human' | 'ai'
    content: str
