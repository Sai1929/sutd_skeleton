"""
Groq / Llama chat client for EHS risk assessment.
Wraps the Groq SDK for use in the FastAPI backend.
"""
from __future__ import annotations

from groq import AsyncGroq

from app.config import settings
from app.services.chat.prompt import SYSTEM_PROMPT

DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class GroqChatClient:
    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL or DEFAULT_MODEL

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 8192,
        image_b64: str | None = None,
        image_mime: str = "image/jpeg",
    ) -> str:
        if image_b64 and messages:
            last = messages[-1]
            if last.get("role") == "user":
                messages = messages[:-1] + [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": last.get("content", "")},
                        {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}},
                    ],
                }]

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
