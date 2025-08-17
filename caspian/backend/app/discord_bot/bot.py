import asyncio
import discord
from sqlalchemy import select
from app.core.config import settings
from app.db.models import SessionLocal, User, Conversation, Message
from app.rag import get_similar_documents

class CaspianBot(discord.Client):
    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if isinstance(message.channel, discord.DMChannel):
            await message.channel.typing()
            # The database operations are now handled in a separate async function
            await self.handle_dm(message)

    async def handle_dm(self, message):
        """
        Handles the entire process of receiving a DM, processing it,
        and sending a response.
        """
        # Lazy import to avoid circular imports at startup
        from app.core.llm import ask_llm

        try:
            async with SessionLocal() as db:
                # 1. Get or create a user for the Discord author
                discord_username = f"discord_{message.author.id}"
                result = await db.execute(
                    select(User).where(User.username == discord_username)
                )
                user = result.scalar_one_or_none()

                if not user:
                    user = User(
                        username=discord_username,
                        hashed_password="",  # Password is not needed for Discord-based users
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)

                # 2. Get or create a conversation for the user
                result = await db.execute(
                    select(Conversation).where(Conversation.user_id == user.id)
                )
                conversation = result.scalar_one_or_none()

                if not conversation:
                    conversation = Conversation(user_id=user.id)
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)

                # 3. Save the user's message to the database
                user_message = Message(
                    conversation_id=conversation.id,
                    sender="user",
                    content=message.content,
                )
                db.add(user_message)
                await db.commit()

                # 4. Retrieve the full conversation history
                history_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.timestamp.asc())
                )
                history = history_result.scalars().all()

                messages_for_llm = [
                    {
                        "role": "system",
                        "content": "You are Caspian, a witty and loyal AI butler. You always address the user as 'Sir' — never 'Madam' or 'Sir/Madam'. Your tone is respectful, charming, and consistent."
                    },
                    *[{"role": msg.sender, "content": msg.content} for msg in history],
                ]

                # 5. RAG Pipeline: Find and inject relevant context
                similar_docs = await get_similar_documents(
                    db, user.id, message.content
                )
                context = "\n".join([doc.content for doc in similar_docs])

                if context:
                    prompt_with_context = (
                        "Given the following context, please answer the user's question."
                        f"\n\nContext:\n{context}\n\nQuestion:\n{message.content}"
                    )
                    # Replace the last message with the context-enhanced one
                    messages_for_llm[-1]["content"] = prompt_with_context

                # 6. Get the response from the language model
                response_text = await ask_llm(messages_for_llm)
                final_reply = response_text.replace("Sir/Madam", "Sir").replace("Madam", "Sir").strip()

                await message.channel.send(final_reply)

                # 7. Save the bot's response to the database
                bot_message = Message(
                    conversation_id=conversation.id,
                    sender="assistant",
                    content=final_reply,
                )
                db.add(bot_message)
                await db.commit()

        except Exception as e:
            await message.channel.send(
                "Apologies, I encountered an error while processing your request."
            )
            print(f"Error in handle_dm: {e}")


def run_bot():
    token = settings.discord_token
    if not token:
        print("DISCORD_TOKEN not set; Discord bot will not start.")
        return

    # Create a new event loop for the new thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    intents = discord.Intents.default()
    intents.message_content = True

    client = CaspianBot(intents=intents)
    client.run(token)