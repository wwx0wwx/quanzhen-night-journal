from __future__ import annotations

import math
from typing import Any

import httpx


class EmbeddingUnavailableError(RuntimeError):
    pass


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
            raise EmbeddingUnavailableError("embedding_not_configured")

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
        except httpx.HTTPError as exc:
            raise EmbeddingUnavailableError(exc.__class__.__name__) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise EmbeddingUnavailableError("embedding_response_invalid") from exc

    async def test_connection(self, *, base_url: str, api_key: str, model_id: str) -> dict[str, Any]:
        try:
            embeddings = await self.embed(
                base_url=base_url,
                api_key=api_key,
                model_id=model_id,
                texts=["embedding probe"],
            )
        except EmbeddingUnavailableError as exc:
            return {"status": "error", "reason": str(exc)}
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
