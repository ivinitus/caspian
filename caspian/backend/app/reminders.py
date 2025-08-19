import asyncio

from datetime import datetime
import discord
from app.core.llm import ask_llm
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
                    from dateutil.relativedelta import relativedelta
                    for reminder in due_reminders:
                        try:
                            # Single-user mode: always send to the bot owner (first user in DB)
                            discord_user = None
                            # Option 1: If you know your Discord user ID, set it here:
                            DISCORD_USER_ID = 1093918301035429938
                            if DISCORD_USER_ID:
                                discord_user = await DISCORD_BOT_INSTANCE.fetch_user(DISCORD_USER_ID)
                            else:
                                # Option 2: fallback to the first user who DMs the bot (not robust, but works for single-user)
                                # You can store the user object globally when the bot receives a DM
                                # For now, skip user lookup and just print a message
                                print(f"[Reminder] Would send: {reminder.content}")
                            if discord_user:
                                # Convert UTC to IST for user-facing message
                                from zoneinfo import ZoneInfo
                                remind_at = reminder.remind_at
                                if remind_at.tzinfo is None:
                                    remind_at = remind_at.replace(tzinfo=ZoneInfo("UTC"))
                                else:
                                    remind_at = remind_at.astimezone(ZoneInfo("UTC"))
                                remind_at_ist = remind_at.astimezone(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                                await discord_user.send(f"Sir, a reminder for you: {reminder.content}\nTime: {remind_at_ist} IST")
                            # Handle recurrence
                            if reminder.recurrence and reminder.recurrence != "none":
                                next_time = None
                                if reminder.recurrence == "daily":
                                    next_time = reminder.remind_at + relativedelta(days=1)
                                elif reminder.recurrence == "weekly":
                                    next_time = reminder.remind_at + relativedelta(weeks=1)
                                elif reminder.recurrence == "monthly":
                                    next_time = reminder.remind_at + relativedelta(months=1)
                                elif reminder.recurrence_rule:
                                    # Custom recurrence: try to parse ISO8601 or cron/rrule (future extension)
                                    pass
                                if next_time:
                                    reminder.remind_at = next_time
                                    reminder.is_sent = False
                                    await db.commit()
                                    print(f"Rescheduled recurring reminder {reminder.id}")
                                else:
                                    reminder.is_sent = True
                                    await db.commit()
                                    print(f"Marked reminder {reminder.id} as sent (no next recurrence)")
                            else:
                                reminder.is_sent = True
                                await db.commit()
                                print(f"Sent reminder {reminder.id}")
                        except Exception as e:
                            print(f"Error sending reminder {reminder.id}: {e}")
        except Exception as e:
            print(f"An error occurred in the reminder checking loop: {e}")
        await asyncio.sleep(5)