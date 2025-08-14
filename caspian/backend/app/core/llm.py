import httpx
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def ask_openai(messages, model="gpt-3.5-turbo"):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
