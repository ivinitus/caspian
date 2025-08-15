import httpx

from app.core.config import settings

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-1.5-flash"


async def ask_gemini(messages, model: str = DEFAULT_MODEL):
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    # Convert OpenAI-style messages to Gemini "contents" format
    # Gemini expects a sequence of contents, each with parts and a role.
    contents = []
    for m in messages:
        role = m.get("role", "user")
        text = m.get("content", "")
        contents.append({
            "role": "model" if role == "assistant" else "user",
            "parts": [{"text": text}],
        })

    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={settings.gemini_api_key}"
    payload = {"contents": contents}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Extract first candidate text
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected Gemini response: {data}") from exc
