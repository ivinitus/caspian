from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.llm import ask_llm
from sqlalchemy import select
from app.db.models import SessionLocal, User, Conversation, Message
from app.rag import get_similar_documents


router = APIRouter(prefix="/llm", tags=["llm"])


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None


@router.post("/chat")
async def chat_with_llm(req: LLMRequest):
    """
    Single-user mode: always use conversation_id=1 and user_id=1.
    """
    try:
        async with SessionLocal() as db:
            conversation_id = 1
            # Fetch all messages for the single conversation
            conv = await db.get(Conversation, conversation_id)
            if not conv:
                conv = Conversation(id=conversation_id)
                db.add(conv)
                await db.commit()
                await db.refresh(conv)
            result = await db.execute(
                select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
            )
            history = result.scalars().all()
            messages = [
                {"role": "assistant" if m.sender == "caspian" else "user", "content": m.content}
                for m in history
            ]
            # Add the new user message
            user_msg = req.messages[-1].content if req.messages else ""
            messages.append({"role": "user", "content": user_msg})

            # Retrieve similar docs for context
            similar_docs = await get_similar_documents(db, 1, user_msg)
            context = "\n".join([doc.content for doc in similar_docs])
            if context:
                prompt_with_context = (
                    "Given the following context, please answer the user's question."
                    f"\n\nContext:\n{context}\n\nQuestion:\n{user_msg}"
                )
                messages[-1]["content"] = prompt_with_context

            # Get LLM reply
            text = await ask_llm(messages, model=req.model)
            reply = text.strip()
            if not reply.lower().startswith("sir"):
                reply = f"Sir, {reply}"

            # Persist user message and assistant reply
            new_user_msg = Message(
                conversation_id=conversation_id,
                content=user_msg,
                sender="user",
            )
            db.add(new_user_msg)
            await db.flush()
            new_assistant_msg = Message(
                conversation_id=conversation_id,
                content=reply,
                sender="caspian",
            )
            db.add(new_assistant_msg)
            await db.commit()

            return {"text": reply}
    except Exception as e:
        print(f"Error in chat_with_llm: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e