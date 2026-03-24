"""
HybridRAGChain — the full RAG query pipeline assembled as a LangChain LCEL chain.

Pipeline:
  QueryProcessor → Intent → SelfQuery/HyDE → Parallel Retrieval
  → RRF Fusion → BGE Reranker → LangChain LCEL → GPT-4o mini → ChatResponse
"""
from __future__ import annotations

import asyncio
import time
import uuid

import numpy as np
import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
from openai import AsyncAzureOpenAI
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.rag import ConversationHistory
from app.schemas.chatbot import ChatResponse, SourceCitation
from app.services.rag.ingestion.embedder import AzureEmbedder
from app.services.rag.query.hyde import HyDEGenerator
from app.services.rag.query.intent_classifier import IntentClassifier, QueryIntent
from app.services.rag.query.self_query_parser import SelfQueryParser
from app.services.rag.retrieval.bm25_retriever import BM25Retriever
from app.services.rag.retrieval.reranker import BGEReranker
from app.services.rag.retrieval.rrf_fusion import RRFFusion
from app.services.rag.retrieval.vector_retriever import RetrievedChunk, VectorRetriever

log = structlog.get_logger()

EHS_SYSTEM_PROMPT = """\
You are an EHS (Environment, Health, Safety) assistant for an inspection portal.
Answer questions directly and conversationally based on the provided inspection records.

Rules:
- For counting questions ("how many"), state the exact number found in context then briefly describe them (activity, hazard, date).
- For factual questions, give a direct 1-3 sentence answer using the context.
- Mention the activity, hazard type, date, and control measures when relevant.
- If context has no relevant records, say "No records found for that query."
- Do NOT use headers like "Data Type:", "Recommendation:", "Safety Focus:" — just answer naturally.
- Keep answers short and to the point.
"""


class HybridRAGChain:
    def __init__(
        self,
        azure_client: AsyncAzureOpenAI,
        langchain_llm: AzureChatOpenAI,
        reranker: BGEReranker,
        db: AsyncSession,
    ) -> None:
        self._client = azure_client
        self._llm = langchain_llm
        self._reranker = reranker
        self._db = db

        self._embedder = AzureEmbedder(azure_client)
        self._intent_clf = IntentClassifier(azure_client)
        self._self_query = SelfQueryParser(azure_client)
        self._hyde = HyDEGenerator(azure_client)
        self._rrf = RRFFusion()

    # ── Public API ────────────────────────────────────────────────

    async def query(
        self,
        query: str,
        conversation_id: str | None = None,
        manual_filters: dict | None = None,
    ) -> ChatResponse:
        start = time.perf_counter()
        conv_id = conversation_id or str(uuid.uuid4())

        # 1. Intent classification
        intent = await self._intent_clf.classify(query)
        log.info("rag.intent", intent=intent, query=query[:80])

        # 2. Build filters and query vector(s)
        filters = manual_filters or {}
        query_embedding: np.ndarray | None = None

        if intent in (QueryIntent.STRUCTURED, QueryIntent.HYBRID):
            sq_result = await self._self_query.parse(query)
            filters = {**filters, **self._self_query.to_filter_dict(sq_result)}
            search_query = sq_result.semantic_query
        else:
            search_query = query

        if intent == QueryIntent.VAGUE:
            query_embedding = await self._hyde.generate_embedding(query)
        else:
            query_embedding = await self._embedder.embed_single(search_query)

        # 3. Sequential dense + sparse retrieval (same DB session — no concurrent ops)
        vector_ret = VectorRetriever(self._db)
        bm25_ret = BM25Retriever(self._db)

        vector_results = await vector_ret.search(query_embedding, filters=filters)
        bm25_results = await bm25_ret.search(search_query, filters=filters)

        # 4. RRF fusion
        fused = self._rrf.fuse(vector_results, bm25_results, top_k=20)

        # 5. Cross-encoder reranking
        reranked = await self._reranker.rerank(query, fused, top_k=settings.RERANKER_TOP_K)

        # 6. Format context
        context = self._format_context(reranked)

        # 7. Load conversation history from DB
        history = await self._load_history(conv_id)

        # 8. Build and run LCEL chain
        answer = await self._run_lcel(query, context, history)

        # 9. Persist conversation turn to DB
        await self._save_turn(conv_id, query, answer)

        latency = round((time.perf_counter() - start) * 1000, 2)

        return ChatResponse(
            conversation_id=conv_id,
            answer=answer,
            query_type=intent.value,
            sources=[self._to_citation(c) for c in reranked],
            retrieved_chunks_count=len(fused),
            reranked_chunks_count=len(reranked),
            latency_ms=latency,
        )

    # ── LCEL chain ────────────────────────────────────────────────

    async def _run_lcel(self, query: str, context: str, history: list) -> str:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=EHS_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context from EHS records:\n{context}\n\nQuestion: {query}"),
        ])
        chain = prompt | self._llm | StrOutputParser()

        return await chain.ainvoke({
            "history": history,
            "context": context,
            "query": query,
        })

    # ── Conversation memory (PostgreSQL) ──────────────────────────

    async def _load_history(self, conv_id: str) -> list:
        result = await self._db.execute(
            select(ConversationHistory.messages)
            .where(ConversationHistory.conv_id == conv_id)
        )
        turns = result.scalar_one_or_none()
        if not turns:
            return []
        turns = turns[-(settings.CONV_MAX_TURNS * 2):]
        messages = []
        for turn in turns:
            if turn["role"] == "human":
                messages.append(HumanMessage(content=turn["content"]))
            elif turn["role"] == "ai":
                messages.append(AIMessage(content=turn["content"]))
        return messages

    async def _save_turn(self, conv_id: str, query: str, answer: str) -> None:
        result = await self._db.execute(
            select(ConversationHistory.messages)
            .where(ConversationHistory.conv_id == conv_id)
        )
        turns = result.scalar_one_or_none() or []
        turns.append({"role": "human", "content": query})
        turns.append({"role": "ai", "content": answer})
        turns = turns[-(settings.CONV_MAX_TURNS * 2):]

        stmt = pg_insert(ConversationHistory).values(
            conv_id=conv_id,
            messages=turns,
        ).on_conflict_do_update(
            index_elements=["conv_id"],
            set_={"messages": turns, "updated_at": func.now()},
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def get_history(self, conv_id: str) -> list[dict]:
        result = await self._db.execute(
            select(ConversationHistory.messages)
            .where(ConversationHistory.conv_id == conv_id)
        )
        return result.scalar_one_or_none() or []

    async def clear_history(self, conv_id: str) -> None:
        await self._db.execute(
            delete(ConversationHistory).where(ConversationHistory.conv_id == conv_id)
        )
        await self._db.commit()

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _format_context(chunks: list[RetrievedChunk]) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"[Source {i} | type={c.source_type} | activity={c.activity_name}]\n{c.chunk_text}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _to_citation(chunk: RetrievedChunk) -> SourceCitation:
        return SourceCitation(
            chunk_id=chunk.id,
            source_type=chunk.source_type,
            source_id=uuid.UUID(chunk.source_id) if chunk.source_id else uuid.uuid4(),
            activity_name=chunk.activity_name,
            chunk_text_preview=chunk.chunk_text[:150],
            relevance_score=chunk.score,
        )
