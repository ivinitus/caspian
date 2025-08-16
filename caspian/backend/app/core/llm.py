from typing import Any

import httpx

from app.core.config import settings

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
OPENAI_API_BASE = "https://api.openai.com/v1"
ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"

DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
}


def _normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]


async def _ask_gemini(messages: list[dict[str, Any]], model: str) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    contents = []
    for m in _normalize_messages(messages):
        contents.append({
            "role": "model" if m["role"] == "assistant" else "user",
            "parts": [{"text": m["content"]}],
        })

    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={settings.gemini_api_key}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json={"contents": contents})
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected Gemini response: {data}") from exc


async def _ask_openai(messages: list[dict[str, Any]], model: str) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    url = f"{OPENAI_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": _normalize_messages(messages),
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected OpenAI response: {data}") from exc


async def _ask_anthropic(messages: list[dict[str, Any]], model: str) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    # Anthropic Messages API
    url = f"{ANTHROPIC_API_BASE}/messages"
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    # Convert to anthropic content format
    content = [
        {
            "role": "user" if m["role"] == "user" else "assistant",
            "content": m["content"],
        }
        for m in _normalize_messages(messages)
    ]
    payload = {"model": model, "max_tokens": 1024, "messages": content}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    try:
        return data["content"][0]["text"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected Anthropic response: {data}") from exc


async def ask_llm(messages: list[dict[str, Any]], model: str | None = None) -> str:
    provider = settings.llm_provider.lower()
    model_to_use = model or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["gemini"])

    if provider == "gemini":
        return await _ask_gemini(messages, model_to_use)
    if provider == "openai":
        return await _ask_openai(messages, model_to_use)
    if provider == "anthropic":
        return await _ask_anthropic(messages, model_to_use)

    raise ValueError(f"Unsupported llm_provider: {settings.llm_provider}")
