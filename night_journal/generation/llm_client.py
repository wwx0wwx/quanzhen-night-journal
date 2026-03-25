from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any


def api_chat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.8,
    max_tokens: int = 900,
    max_retries: int = 3,
    timeout: int = 150,
) -> str:
    """
    调用 OpenAI 兼容接口生成文本，支持自动重试机制。

    Args:
        base_url: API 基础 URL
        api_key: API 密钥
        model: 模型名称
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数
        max_retries: 最大重试次数（默认 3）
        timeout: 超时时间（秒，默认 150）

    Returns:
        生成的文本内容

    Raises:
        RuntimeError: 所有重试失败后抛出异常
    """
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )

    last_error = None

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode('utf-8'))
                content = body['choices'][0]['message']['content'].strip()
                return content

        except urllib.error.HTTPError as e:
            last_error = f'HTTP {e.code}: {e.reason}'
            # 429 (Too Many Requests) 或 5xx 错误可以重试
            if e.code == 429 or e.code >= 500:
                wait_time = (2 ** attempt) * 2  # 指数退避: 2, 4, 8 秒
                time.sleep(wait_time)
                continue
            else:
                # 4xx 错误（除了 429）直接失败
                raise RuntimeError(f'API 请求失败（HTTP {e.code}）: {e.reason}')

        except urllib.error.URLError as e:
            last_error = f'网络错误: {e.reason}'
            # 连接超时等网络错误可以重试
            wait_time = (2 ** attempt) * 2
            time.sleep(wait_time)
            continue

        except (json.JSONDecodeError, KeyError) as e:
            # 响应格式错误，重试可能无益，直接失败
            raise RuntimeError(f'API 响应解析失败: {e}')

        except TimeoutError:
            last_error = '请求超时'
            wait_time = (2 ** attempt) * 2
            time.sleep(wait_time)
            continue

    # 所有重试都失败
    raise RuntimeError(f'API 请求失败（已重试 {max_retries} 次）: {last_error}')
