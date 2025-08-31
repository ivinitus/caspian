from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.llm import ask_llm
from sqlalchemy import select
from app.db.models import SessionLocal, User, Conversation, Message
from app.rag import rag_system
from app.core.personality import get_chat_prompt


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
            # Get user info
            user = await db.get(User, 1)  # In single-user mode
            username = user.username if user else None

            # Initialize messages with system prompt
            messages = [
                {"role": "system", "content": get_chat_prompt(user_id=1, username=username)}
            ]
            
            # Add conversation history
            messages.extend([
                {"role": "assistant" if m.sender == "caspian" else "user", "content": m.content}
                for m in history
            ])
            
            # Add the new user message
            user_msg = req.messages[-1].content if req.messages else ""
            messages.append({"role": "user", "content": user_msg})

            # Retrieve relevant context (documents and memories)
            context_data = await rag_system.get_similar_documents(db, 1, user_msg)
            
            # Combine documents and memories into context
            doc_context = "\n".join([doc.content for doc in context_data["documents"]])
            memory_context = "\n".join([
                f"{mem.content} (from memory)" 
                for mem in context_data["memories"]["long_term"]
            ])
            recent_context = "\n".join([
                f"{msg['content']} ({msg['type']})" 
                for msg in context_data["memories"]["short_term"]
            ])
            
            # Build full context string
            context_parts = []
            if doc_context:
                context_parts.append("Documents:\n" + doc_context)
            if memory_context:
                context_parts.append("Related Memories:\n" + memory_context)
            if recent_context:
                context_parts.append("Recent Context:\n" + recent_context)
            
            full_context = "\n\n".join(context_parts)
            
            if full_context:
                prompt_with_context = (
                    "Given the following context, please answer the user's question. "
                    "Use the context to provide more personalized and contextually relevant responses."
                    f"\n\nContext:\n{full_context}\n\nQuestion:\n{user_msg}"
                )
                messages[-1]["content"] = prompt_with_context

            # Get LLM reply
            text = await ask_llm(messages, model=req.model)
            reply = text.strip()
            # Remove forced 'Sir' prefix; let personality and prompt handle address naturally

            # Persist user message and assistant reply
            new_user_msg = Message(
                conversation_id=conversation_id,
                content=user_msg,
                sender="user",
            )
            db.add(new_user_msg)
            await db.flush()
            
            # Store user message in memory
            await rag_system.add_to_memory(
                db,
                user_id=1,
                message={
                    "content": user_msg,
                    "type": "user_message"
                }
            )
            
            new_assistant_msg = Message(
                conversation_id=conversation_id,
                content=reply,
                sender="caspian",
            )
            db.add(new_assistant_msg)
            
            # Store assistant reply in memory
            await rag_system.add_to_memory(
                db,
                user_id=1,
                message={
                    "content": reply,
                    "type": "assistant_message"
                }
            )
            
            await db.commit()

            return {"text": reply}
    except Exception as e:
        print(f"Error in chat_with_llm: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e