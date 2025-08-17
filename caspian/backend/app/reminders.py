import asyncio
from datetime import datetime
import discord
from sqlalchemy import select
from app.db.models import Reminder, SessionLocal, User

DISCORD_BOT_INSTANCE = None

async def check_reminders_periodically():
    while True:
        try:
            now = datetime.utcnow()
            async with SessionLocal() as db:
                result = await db.execute(
                    select(Reminder).where(
                        Reminder.remind_at <= now,
                        Reminder.is_sent == False
                    )
                )
                due_reminders = result.scalars().all()

                if due_reminders and DISCORD_BOT_INSTANCE:
                    for reminder in due_reminders:
                        try:
                            user_result = await db.execute(select(User).where(User.id == reminder.user_id))
                            user = user_result.scalar_one_or_none()
                            if user and user.discord_id:
                                discord_user = await DISCORD_BOT_INSTANCE.fetch_user(user.discord_id)
                                if discord_user:
                                    await discord_user.send(f"Sir, a reminder for you: {reminder.content}")
                                    reminder.is_sent = True
                                    await db.commit()
                                    print(f"Sent reminder {reminder.id} to user {reminder.user_id}")
                            else:
                                print(f"User or discord_id not found for reminder {reminder.id}")
                                reminder.is_sent = True # Mark as sent to avoid retries
                                await db.commit()
                        except discord.NotFound:
                            print(f"Could not find Discord user with ID: {user.discord_id} for reminder {reminder.id}")
                            reminder.is_sent = True
                            await db.commit()
                        except Exception as e:
                            print(f"Error sending reminder {reminder.id}: {e}")
        except Exception as e:
            print(f"An error occurred in the reminder checking loop: {e}")
        
        await asyncio.sleep(60)