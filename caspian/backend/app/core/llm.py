import httpx

from app.core.config import settings

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


async def ask_openai(messages, model="gpt-3.5-turbo"):
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": messages,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
