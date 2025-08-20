"""
Command-line interface for interacting with Caspian.
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from sqlalchemy import select
from app.db.models import SessionLocal, User, Conversation, Message
from app.core.llm import ask_llm
from app.core.personality import get_chat_prompt
from app.rag import rag_system

async def chat_with_caspian():
    print("\n=== Caspian Terminal Interface ===")
    print("Type 'exit' to quit, 'clear' to start a new conversation\n")
    
    async with SessionLocal() as db:
        conversation_id = 1
        # Initialize or get conversation
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            conv = Conversation(id=conversation_id)
            db.add(conv)
            await db.commit()

        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("\nCaspian: Goodbye, Sir. I'll be here when you need me.")
                    break
                    
                if user_input.lower() == 'clear':
                    # Clear conversation history
                    await db.execute(select(Message).where(Message.conversation_id == conversation_id))
                    await db.commit()
                    print("\nCaspian: Conversation history cleared, Sir.")
                    continue

                if not user_input:
                    continue

                # Get conversation history
                result = await db.execute(
                    select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
                )
                history = result.scalars().all()
                
                # Prepare messages with system prompt
                messages = [
                    {"role": "system", "content": get_chat_prompt(user_id=1, username="Vinitus")}
                ]
                messages.extend([
                    {"role": "assistant" if m.sender == "caspian" else "user", "content": m.content}
                    for m in history
                ])
                messages.append({"role": "user", "content": user_input})

                # Get context from RAG system
                context_data = await rag_system.get_similar_documents(db, 1, user_input)
                
                # Add context to the prompt if available
                if context_data["documents"] or context_data["memories"]:
                    doc_context = "\n".join(doc.content for doc in context_data["documents"])
                    memory_context = "\n".join(
                        f"{mem.content}" for mem in context_data["memories"].get("long_term", [])
                    )
                    context = f"Context:\n{doc_context}\n{memory_context}\n\nQuery:\n{user_input}"
                    messages[-1]["content"] = context

                # Get Caspian's response
                response = await ask_llm(messages)

                # Store messages
                user_msg = Message(
                    conversation_id=conversation_id,
                    content=user_input,
                    sender="user",
                )
                db.add(user_msg)
                
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    content=response,
                    sender="caspian",
                )
                db.add(assistant_msg)
                
                await db.commit()

                # Store in memory system
                await rag_system.add_to_memory(
                    db,
                    user_id=1,
                    message={
                        "content": user_input,
                        "type": "user_message",
                        "platform": "terminal"
                    }
                )

                print("\nCaspian:", response)

            except KeyboardInterrupt:
                print("\n\nCaspian: Goodbye, Sir. I'll be here when you need me.")
                break
            except Exception as e:
                print(f"\nCaspian: I apologize, Sir. An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(chat_with_caspian())
