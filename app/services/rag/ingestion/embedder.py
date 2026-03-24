"""
AzureEmbedder — batch embedding using Azure text-embedding-3-small.
Includes exponential backoff retry and L2 normalisation.
"""
from __future__ import annotations

import asyncio
import math

import numpy as np
import structlog
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

log = structlog.get_logger()


class AzureEmbedder:
    def __init__(self, client: AsyncAzureOpenAI) -> None:
        self._client = client
        self._deployment = settings.AZURE_OPENAI_EMBED_DEPLOYMENT
        self._dims = settings.AZURE_OPENAI_EMBED_DIMS
        self._batch_size = settings.EMBED_BATCH_SIZE

    @retry(
        stop=stop_after_attempt(settings.EMBED_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=settings.EMBED_RETRY_BASE_DELAY,
            min=settings.EMBED_RETRY_BASE_DELAY,
            max=30,
        ),
        reraise=True,
    )
    async def _embed_batch_raw(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._deployment,
            input=texts,
            dimensions=self._dims,
        )
        return [item.embedding for item in response.data]

    async def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        """
        Embed texts in batches of EMBED_BATCH_SIZE.
        Returns L2-normalised numpy arrays (shape: (1536,)).
        """
        if not texts:
            return []

        all_embeddings: list[np.ndarray] = []
        n_batches = math.ceil(len(texts) / self._batch_size)

        for i in range(n_batches):
            batch = texts[i * self._batch_size : (i + 1) * self._batch_size]
            log.debug("embedding.batch", batch_num=i + 1, total=n_batches, size=len(batch))
            raw = await self._embed_batch_raw(batch)

            for vec in raw:
                arr = np.array(vec, dtype=np.float32)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm
                all_embeddings.append(arr)

        return all_embeddings

    async def embed_single(self, text: str) -> np.ndarray:
        results = await self.embed_batch([text])
        return results[0]
