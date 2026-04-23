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
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
