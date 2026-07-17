"""Unified LLM routing: prefer local Ollama, fall back to DeepSeek cloud."""

from __future__ import annotations

from typing import Any

from app.ai import deepseek_client
from app.ai import ollama_client


def chat_prefer_ollama(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    format_json: bool = False,
    timeout: int = 180,
) -> dict[str, Any]:
    """
    Call LLM with priority:
      1) Local Ollama (system install or bundled runtime)
      2) DeepSeek cloud (needs DEEPSEEK_API_KEY in .env)
    Returns {ok, content, model?, provider?, error?}.
    """
    try:
        from app.ai.ollama_runtime import ensure_ollama_ready

        ensure_ollama_ready()
    except Exception:
        pass

    ollama = ollama_client.chat_messages(
        messages,
        temperature=temperature,
        format_json=format_json,
        timeout=timeout,
    )
    if ollama.get("ok"):
        ollama["provider"] = "ollama"
        return ollama

    ds_health = deepseek_client.check_health()
    if ds_health.get("configured"):
        # DeepSeek OpenAI API has no native format=json flag; ask in prompt instead.
        result = deepseek_client.chat(
            messages,
            temperature=temperature,
            timeout=min(timeout, 120),
        )
        if result.get("ok"):
            result["provider"] = "deepseek"
            return result
        return {
            "ok": False,
            "error": "；".join(
                [
                    ollama.get("error") or "Ollama 不可用",
                    result.get("error") or "DeepSeek 调用失败",
                ]
            ),
            "provider": None,
        }

    return {
        "ok": False,
        "error": (ollama.get("error") or "Ollama 不可用")
        + "；未配置 DEEPSEEK_API_KEY，无法走云端备用",
        "provider": None,
    }


def chat_text_prefer_ollama(
    user: str,
    *,
    system: str | None = None,
    temperature: float = 0.3,
    format_json: bool = True,
    timeout: int = 180,
) -> dict[str, Any]:
    """Convenience: system + user → {ok, content, provider}."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    return chat_prefer_ollama(
        messages,
        temperature=temperature,
        format_json=format_json,
        timeout=timeout,
    )
