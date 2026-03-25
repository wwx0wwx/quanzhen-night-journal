from __future__ import annotations

import json
import urllib.request
from typing import Any


def api_chat(base_url: str, api_key: str, model: str, messages: list[dict[str, Any]], temperature: float = 0.8, max_tokens: int = 900) -> str:
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
    with urllib.request.urlopen(req, timeout=150) as resp:
        body = json.loads(resp.read().decode('utf-8'))
    return body['choices'][0]['message']['content'].strip()
