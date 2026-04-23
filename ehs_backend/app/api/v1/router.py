from fastapi import APIRouter

from app.api.v1 import chat, inspect, quiz

router = APIRouter(prefix="/api/v1")

router.include_router(inspect.router)
router.include_router(quiz.router)
router.include_router(chat.router)

# sessions.py and submissions.py parked — require DB + auth
# chatbot.py parked — RAG pipeline (pgvector + BGE reranker)

# RAG chatbot parked — code preserved in app/api/v1/chatbot.py and app/services/rag/
# To re-enable: from app.api.v1 import chatbot; router.include_router(chatbot.router)
