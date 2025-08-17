import asyncio
import discord
from sqlalchemy import select
from app.core.config import settings
from app.db.models import SessionLocal, User, Conversation, Message
from app.rag import get_similar_documents

class CaspianBot(discord.Client):
    def __init__(self, *args, **kwargs):
        self.main_loop = kwargs.pop('main_loop')
        self.on_ready_callback = kwargs.pop('on_ready_callback')
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")
        if self.on_ready_callback:
            self.on_ready_callback(self)

    async def on_message(self, message):
        if message.author == self.user:
            return
        if isinstance(message.channel, discord.DMChannel):
            try:
                await message.channel.typing()
                future = asyncio.run_coroutine_threadsafe(
                    self._process_and_get_reply(message), self.main_loop
                )
                final_reply = await asyncio.wrap_future(future)
                if final_reply:
                    await message.channel.send(final_reply)
            except Exception as e:
                print(f"!!! ERROR during bot orchestration: {e} !!!")
                await message.channel.send("My apologies, Sir. A critical error occurred.")

    async def _process_and_get_reply(self, message) -> str | None:
        from app.core.llm import ask_llm
        try:
            async with SessionLocal() as db:
                user_result = await db.execute(select(User).where(User.username == "sir"))
                user = user_result.scalar_one_or_none()
                if not user:
                    print("CRITICAL: Default user 'sir' not found.")
                    return "Apologies, Sir. I am experiencing a critical system error."

                if not user.discord_id:
                    user.discord_id = str(message.author.id)
                    await db.commit()
                    print(f"Associated Discord ID {message.author.id} with user 'sir'.")

                stmt = (
                    select(Conversation)
                    .where(Conversation.user_id == user.id)
                    .order_by(Conversation.started_at.desc())
                )
                result = await db.execute(stmt)
                conversation = result.scalars().first()

                if not conversation:
                    conversation = Conversation(user_id=user.id)
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)

                user_message = Message(
                    conversation_id=conversation.id, sender="user", content=message.content
                )
                db.add(user_message)
                await db.commit()

                history_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.timestamp.asc())
                )
                history = history_result.scalars().all()

                messages_for_llm = [
                    {"role": "system", "content": "You are Caspian..."},
                    *[{"role": msg.sender, "content": msg.content} for msg in history]
                ]

                similar_docs = await get_similar_documents(db, user.id, message.content)
                context = "\n".join([doc.content for doc in similar_docs])
                if context:
                    messages_for_llm[-1]["content"] = f"Context:\n{context}\n\nQuestion:\n{message.content}"
                
                response_text = await ask_llm(messages_for_llm)
                final_reply = response_text.replace("Sir/Madam", "Sir").replace("Madam", "Sir").strip()
                
                bot_message = Message(
                    conversation_id=conversation.id, sender="assistant", content=final_reply
                )
                db.add(bot_message)
                await db.commit()
                
                return final_reply
        except Exception as e:
            print(f"!!! ERROR in backend logic for bot: {e} !!!")
            return None

def run_bot(main_loop: asyncio.AbstractEventLoop, on_ready_callback):
    token = settings.discord_token
    if not token:
        print("DISCORD_TOKEN not set; Discord bot will not start.")
        return
    intents = discord.Intents.default()
    intents.message_content = True
    client = CaspianBot(intents=intents, main_loop=main_loop, on_ready_callback=on_ready_callback)
    client.run(token)