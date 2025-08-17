from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.llm import ask_llm
from app.db.models import SessionLocal, User
from app.rag import get_similar_documents
from app.api.dependencies import get_current_user


router = APIRouter(prefix="/llm", tags=["llm"])


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None


@router.post("/chat")
async def chat_with_llm(req: LLMRequest, current_user: User = Depends(get_current_user)):
    try:
        # Convert all incoming messages to dictionaries first
        messages = [m.model_dump() for m in req.messages]
        last_message_content = messages[-1]["content"]

        async with SessionLocal() as db:
            # Use the authenticated user's ID for document retrieval
            similar_docs = await get_similar_documents(
                db, current_user.id, last_message_content
            )

        context = "\n".join([doc.content for doc in similar_docs])

        # Only add context if it's found
        if context:
            prompt_with_context = (
                "Given the following context, please answer the user's question."
                f"\n\nContext:\n{context}\n\nQuestion:\n{last_message_content}"
            )
            # Replace the last user message with the context-aware prompt
            messages[-1]["content"] = prompt_with_context

        text = await ask_llm(messages, model=req.model)
        reply = text.strip()

        # The LLM might include "Sir," so we handle that gracefully
        if not reply.lower().startswith("sir"):
            reply = f"Sir, {reply}"

        return {"text": reply}
    except Exception as e:
        # Provide more detailed error logging on the backend
        print(f"Error in chat_with_llm: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e