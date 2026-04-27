"""
Groq / Llama risk assessment chatbot endpoint.
Replaces the RAG chatbot for the active API — RAG code is preserved but parked.
"""
import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_chat_client
from app.schemas.chat import ChatMessage, ChatResponseOut
from app.services.chat.client import GroqChatClient

router = APIRouter(prefix="/chat", tags=["chat"])

_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/query", response_model=ChatResponseOut)
async def chat_query(
    message: Annotated[str, Form()] = "",
    history: Annotated[str, Form()] = "[]",
    image: Annotated[UploadFile | None, File()] = None,
    client: GroqChatClient = Depends(get_chat_client),
) -> ChatResponseOut:
    if not message.strip() and image is None:
        raise HTTPException(status_code=422, detail="Provide a message or image.")

    try:
        history_data = json.loads(history)
        parsed_history = [ChatMessage(**m) for m in history_data]
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid history JSON.")

    image_b64: str | None = None
    image_mime = "image/jpeg"

    if image is not None:
        mime = image.content_type or "image/jpeg"
        if mime not in _ALLOWED_MIME:
            raise HTTPException(status_code=422, detail=f"Unsupported image type: {mime}.")
        data = await image.read()
        if len(data) > _MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit.")
        image_b64 = base64.b64encode(data).decode()
        image_mime = mime

    # When image-only, give the LLM a prompt to analyse what it sees
    user_text = message.strip() or "Please analyse this image and identify any workplace hazards, risks, and recommended control measures."

    messages = [{"role": m.role, "content": m.content} for m in parsed_history]
    messages.append({"role": "user", "content": user_text})

    reply = await client.chat(messages, image_b64=image_b64, image_mime=image_mime)

    return ChatResponseOut(reply=reply, model=client._model)
