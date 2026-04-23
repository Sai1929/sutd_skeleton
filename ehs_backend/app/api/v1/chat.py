"""
Groq / Llama risk assessment chatbot endpoint.
Replaces the RAG chatbot for the active API — RAG code is preserved but parked.
"""
from fastapi import APIRouter, Depends

from app.dependencies import get_chat_client
from app.schemas.chat import ChatRequest, ChatResponseOut
from app.services.chat.client import GroqChatClient

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponseOut)
async def chat_query(
    body: ChatRequest,
    client: GroqChatClient = Depends(get_chat_client),
) -> ChatResponseOut:
    messages = [{"role": m.role, "content": m.content} for m in body.history]
    messages.append({"role": "user", "content": body.message})

    reply = await client.chat(messages)

    return ChatResponseOut(
        reply=reply,
        model=client._model,
    )
