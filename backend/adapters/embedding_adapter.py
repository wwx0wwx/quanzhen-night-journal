from __future__ import annotations

import hashlib
import math
from typing import Any

import httpx

from backend.config import get_settings


class EmbeddingAdapter:
    async def embed(
        self,
        *,
        base_url: str,
        api_key: str,
        model_id: str,
        texts: list[str],
        dimensions: int = 1536,
    ) -> list[list[float]]:
        if not base_url or not api_key or not model_id:
            return [self._fake_vector(text, dimensions) for text in texts]

        payload = {"model": model_id, "input": texts}
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/embeddings",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
            return [item["embedding"] for item in data["data"]]
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return [self._fake_vector(text, dimensions) for text in texts]

    async def test_connection(self, *, base_url: str, api_key: str, model_id: str) -> dict[str, Any]:
        embeddings = await self.embed(
            base_url=base_url,
            api_key=api_key,
            model_id=model_id,
            texts=["全真夜记 embedding probe"],
        )
        return {"dimensions": len(embeddings[0]) if embeddings else 0}

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        length = min(len(a), len(b))
        numerator = sum(a[i] * b[i] for i in range(length))
        denom_a = math.sqrt(sum(v * v for v in a[:length]))
        denom_b = math.sqrt(sum(v * v for v in b[:length]))
        if not denom_a or not denom_b:
            return 0.0
        return numerator / (denom_a * denom_b)

    def _fake_vector(self, text: str, dimensions: int) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector: list[float] = []
        while len(vector) < dimensions:
            for byte in digest:
                vector.append((byte / 255.0) - 0.5)
                if len(vector) >= dimensions:
                    break
            digest = hashlib.sha256(digest).digest()
        return vector
