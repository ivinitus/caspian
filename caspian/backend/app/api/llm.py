from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import ask_llm
from app.db.models import SessionLocal
from app.rag import get_similar_documents

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None  # optional override


@router.post("/chat")
async def chat_with_llm(req: LLMRequest):
    try:
        user_id_for_rag = 1
        async with SessionLocal() as db:
            last_message = req.messages[-1].content
            similar_docs = await get_similar_documents(
                db, user_id_for_rag, last_message
            )

        context = "\n".join([doc.content for doc in similar_docs])
        prompt_with_context = (
            "Given the following context, please answer the user's question."
            f"\n\nContext:\n{context}\n\nQuestion:\n{last_message}"
        )

        messages_for_llm = req.messages[:-1] + [
            {"role": "user", "content": prompt_with_context}
        ]

        text = await ask_llm(
            [m.dict() for m in messages_for_llm], model=req.model
        )
        reply = text.strip()
        if not reply.lower().startswith("sir"):
            reply = f"Sir, {reply}"
        return {"text": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None
