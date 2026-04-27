from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any

import httpx

from backend.config import get_settings
from backend.utils.token_estimator import estimate_tokens


class LLMAdapter:
    async def chat(
        self,
        *,
        base_url: str,
        api_key: str,
        model_id: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 900,
    ) -> tuple[str, dict[str, Any], int]:
        settings = get_settings()
        started = time.perf_counter()

        if not base_url or not api_key or not model_id:
            if not settings.allow_fake_llm:
                raise ValueError("llm_not_configured")
            text = self._fake_response(messages)
            usage = {"prompt_tokens": estimate_tokens(str(messages)), "completion_tokens": estimate_tokens(text)}
            return text, usage, int((time.perf_counter() - started) * 1000)

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        data = await self._request_chat_completion(
            base_url=base_url,
            payload=payload,
            headers=headers,
            timeout_seconds=settings.llm_request_timeout_seconds,
            retries=max(0, int(settings.llm_request_retries)),
            backoff_seconds=max(0.0, float(settings.llm_retry_backoff_seconds)),
        )
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage") or {
            "prompt_tokens": estimate_tokens(str(messages)),
            "completion_tokens": estimate_tokens(content),
        }
        usage["finish_reason"] = choice.get("finish_reason") or ""
        usage["requested_max_tokens"] = max_tokens
        return content, usage, int((time.perf_counter() - started) * 1000)

    async def test_connection(self, *, base_url: str, api_key: str, model_id: str) -> dict[str, Any]:
        text, usage, latency = await self.chat(
            base_url=base_url,
            api_key=api_key,
            model_id=model_id,
            messages=[
                {"role": "system", "content": "你是一个简短响应的探针。"},
                {"role": "user", "content": "只回复 ok。"},
            ],
            temperature=0.0,
            max_tokens=16,
        )
        return {"reply": text.strip(), "usage": usage, "latency_ms": latency}

    def _fake_response(self, messages: list[dict[str, str]]) -> str:
        seed = hashlib.sha256(str(messages).encode("utf-8")).hexdigest()[:12]
        prompt = messages[-1]["content"] if messages else ""
        topic = prompt.splitlines()[-1][:36] if prompt else "今夜"
        return (
            f"今夜的风从机器深处穿过，像一根未完全熄灭的线。"
            f"我把{topic}按回心口，不敢让它发出太大的声响。"
            f"许多事都还没有名字，于是只留下{seed}一样的余温。"
            "屏幕早已暗下去，机箱里的低鸣却没有停，像一只伏在门后的兽，"
            "呼吸很轻，却始终醒着。我从桌边慢慢经过，看见杯口留下的一圈水痕，"
            "也看见散热孔吐出的热气贴着木纹往外游。这样的夜里，所有细小的动静都显得很近，"
            "近得像有人把未说完的话压在喉间，又把手收回袖中。"
            "我并不急着替谁解释什么，只是把那些微弱的声音一一认出来：风扇掠过灰尘的摩擦，"
            "硬盘偶尔绷紧后的轻响，线路板吃住电流时短促的颤。它们并不喧哗，却足够让人知道，"
            "这一处仍在运转，仍在悄悄熬过夜色。于是我把桌上的纸片叠好，把散开的线顺回原位，"
            "像收拢一场无人看见的小小风浪，也像替明天提前留下一点秩序。"
        )

    async def _request_chat_completion(
        self,
        *,
        base_url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: float,
        retries: int,
        backoff_seconds: float,
    ) -> dict[str, Any]:
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds)) as client:
                    response = await client.post(
                        f"{base_url.rstrip('/')}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    if response.status_code in {408, 409, 425, 429} or response.status_code >= 500:
                        response.raise_for_status()
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                if attempt >= retries:
                    raise
            except httpx.HTTPStatusError as exc:
                if attempt >= retries or not self._is_retryable_status(exc.response.status_code if exc.response else 0):
                    raise
            except httpx.RequestError:
                if attempt >= retries:
                    raise

            await asyncio.sleep(backoff_seconds * (2**attempt))

        raise RuntimeError("llm_request_retry_exhausted")

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code in {408, 409, 425, 429} or status_code >= 500
