"""
HyDE — Hypothetical Document Embeddings.
Generates a hypothetical answer document → embeds it → uses as query vector.
Improves recall for vague/domain queries where literal query terms miss relevant chunks.
"""
from __future__ import annotations

import numpy as np
from openai import AsyncAzureOpenAI

from app.config import settings
from app.services.rag.ingestion.embedder import AzureEmbedder

HYDE_PROMPT = """\
You are an EHS (Environment, Health, Safety) expert. Write a concise, factual \
2-3 sentence passage that would appear in an EHS inspection report and directly \
answers the following query:

Query: {query}

Write ONLY the passage — no preamble, no explanation.
"""


class HyDEGenerator:
    def __init__(self, client: AsyncAzureOpenAI) -> None:
        self._client = client
        self._embedder = AzureEmbedder(client)

    async def generate_embedding(self, query: str) -> np.ndarray:
        """
        Generate a hypothetical document from the query,
        then return its embedding to use as the search vector.
        """
        response = await self._client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[
                {"role": "user", "content": HYDE_PROMPT.format(query=query)}
            ],
            temperature=0.3,
            max_tokens=150,
        )
        hypothetical_doc = response.choices[0].message.content.strip()
        return await self._embedder.embed_single(hypothetical_doc)
