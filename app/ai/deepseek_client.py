"""DeepSeek API client — deepseek-v4-flash, non-thinking mode.

Official docs:
- https://api-docs.deepseek.com/
- https://api-docs.deepseek.com/guides/thinking_mode

Defaults (latest V4 API):
- model: deepseek-v4-flash
- thinking: {"type": "disabled"}  # non-thinking mode
- base_url: https://api.deepseek.com
"""

from __future__ import annotations

from typing import Any

import requests

from app.utils.config import deepseek_settings


def check_health() -> dict[str, Any]:
    cfg = deepseek_settings()
    if not cfg["api_key"]:
        return {
            "ok": False,
            "configured": False,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "message": "未配置 DEEPSEEK_API_KEY（请写入项目根目录 .env）",
        }
    return {
        "ok": True,
        "configured": True,
        "model": cfg["model"],
        "base_url": cfg["base_url"],
        "message": f"DeepSeek 已配置 · {cfg['model']} · 非思考模式",
    }


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = 0.7,
    timeout: int = 120,
) -> dict[str, Any]:
    """Chat Completions in non-thinking mode (flash).

    Uses OpenAI-compatible endpoint:
    POST {base_url}/chat/completions
    with body field thinking.type = disabled.
    """
    cfg = deepseek_settings()
    if not cfg["api_key"]:
        return {"ok": False, "error": "未配置 DEEPSEEK_API_KEY"}

    use_model = model or cfg["model"]
    url = f"{cfg['base_url']}/chat/completions"
    payload: dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "stream": False,
        # Official non-thinking toggle (default is enabled for V4)
        "thinking": {"type": "disabled"},
    }
    # Non-thinking mode supports sampling params; thinking mode ignores them.
    if temperature is not None:
        payload["temperature"] = temperature

    try:
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if r.status_code >= 400:
            detail = r.text[:500]
            return {
                "ok": False,
                "error": f"DeepSeek HTTP {r.status_code}: {detail}",
                "status_code": r.status_code,
            }
        data = r.json()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        return {
            "ok": True,
            "content": content,
            "model": data.get("model") or use_model,
            "usage": data.get("usage") or {},
            "raw": data,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def chat_text(
    user: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float | None = 0.7,
) -> str | None:
    """Convenience wrapper: return assistant text or None on failure."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    result = chat(messages, model=model, temperature=temperature)
    if not result.get("ok"):
        return None
    text = (result.get("content") or "").strip()
    return text or None
