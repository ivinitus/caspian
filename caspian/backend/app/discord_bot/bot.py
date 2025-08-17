import asyncio
import discord
from sqlalchemy import select
from app.core.config import settings
from app.db.models import SessionLocal, User, Conversation, Message, Reminder
from app.rag import get_similar_documents
from datetime import datetime
import json
from app.api.auth import get_password_hash
import secrets

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
                if message.content.startswith('!remind'):
                    future = asyncio.run_coroutine_threadsafe(
                        self._handle_reminder_command(message), self.main_loop
                    )
                    reply = await asyncio.wrap_future(future)
                else:
                    future = asyncio.run_coroutine_threadsafe(
                        self._process_and_get_reply(message), self.main_loop
                    )
                    reply = await asyncio.wrap_future(future)

                if reply:
                    await message.channel.send(reply)
            except Exception as e:
                print(f"!!! ERROR during bot orchestration: {e} !!!")
                await message.channel.send("My apologies, Sir. A critical error occurred.")

    async def _handle_reminder_command(self, message) -> str:
        from app.core.llm import ask_llm
        try:
            now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            prompt = f"""
            Given the user's reminder request and the current UTC time, extract the reminder content and the exact time for the reminder.
            The current time is: {now_utc} UTC.
            User request: "{message.content}"
            Please return a JSON object with two keys: "remind_at" (in YYYY-MM-DD HH:MM:SS format, UTC) and "content".
            """
            messages_for_llm = [{"role": "user", "content": prompt}]
            response_text = await ask_llm(messages_for_llm)
            
            json_response_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            reminder_data = json.loads(json_response_str)

            remind_at_str = reminder_data.get("remind_at")
            content = reminder_data.get("content")

            if not remind_at_str or not content:
                return "I'm sorry, Sir, I could not understand the reminder. Please try again."
                
            remind_at = datetime.strptime(remind_at_str, '%Y-%m-%d %H:%M:%S')

            async with SessionLocal() as db:
                user_result = await db.execute(select(User).where(User.discord_id == str(message.author.id)))
                user = user_result.scalar_one_or_none()
                if not user:
                    dummy_password = secrets.token_hex(16)
                    hashed_pw = get_password_hash(dummy_password)
                    user = User(username=message.author.name, discord_id=str(message.author.id), hashed_password=hashed_pw)
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)

                new_reminder = Reminder(
                    user_id=user.id,
                    content=content,
                    remind_at=remind_at,
                )
                db.add(new_reminder)
                await db.commit()
            
            return f"Very good, Sir. I will remind you about '{content}' at {remind_at_str} UTC."

        except Exception as e:
            print(f"!!! ERROR in reminder handling: {e} !!!")
            return "I'm sorry, Sir, I encountered an error while setting your reminder."


    async def _process_and_get_reply(self, message) -> str | None:
        from app.core.llm import ask_llm
        try:
            async with SessionLocal() as db:
                user_result = await db.execute(select(User).where(User.discord_id == str(message.author.id)))
                user = user_result.scalar_one_or_none()
                if not user:
                    dummy_password = secrets.token_hex(16)
                    hashed_pw = get_password_hash(dummy_password)
                    user = User(username=message.author.name, discord_id=str(message.author.id), hashed_password=hashed_pw)
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)

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