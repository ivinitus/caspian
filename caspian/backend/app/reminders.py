import asyncio
import concurrent.futures
import logging
from datetime import datetime
import discord
from app.core.llm import ask_llm
from sqlalchemy import select
from app.db.models import Reminder, SessionLocal, User
import traceback

# Configure logging - set to WARNING level to keep terminal clean
logging.basicConfig(level=logging.WARNING, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("reminders")

# Single user ID - this is you
OWNER_USER_ID = 1093918301035429938

DISCORD_BOT_INSTANCE = None
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5

def register_bot_instance(bot_instance):
    """Register the bot instance for sending reminders."""
    global DISCORD_BOT_INSTANCE
    DISCORD_BOT_INSTANCE = bot_instance

async def send_discord_reminder(bot, user_id, content, remind_at_ist, retry_count=0):
    """Send a reminder to a Discord user using the bot's loop."""
    try:
        if bot and bot.loop:
            # Get the event loop from the bot
            loop = bot.loop
            
            # Define a function to be executed in the bot's event loop
            async def _send_message():
                try:
                    discord_user = await bot.fetch_user(user_id)
                    if discord_user:
                        await discord_user.send(f"Sir, a reminder for you: {content}\nTime: {remind_at_ist} IST")
                        return True
                    else:
                        return False
                except discord.errors.Forbidden:
                    logger.error(f"Bot does not have permission to send DM to user {user_id}")
                    return False
                except Exception as e:
                    logger.error(f"Error in _send_message: {e}")
                    return False
            
            # Run the coroutine in the bot's event loop
            if asyncio.get_event_loop() == loop:
                # We're already in the bot's event loop
                return await _send_message()
            else:
                # We need to run the coroutine in the bot's event loop
                future = asyncio.run_coroutine_threadsafe(_send_message(), loop)
                # Wait for the result with a timeout
                return future.result(timeout=10)
        else:
            return False
    except concurrent.futures.TimeoutError:
        if retry_count < MAX_RETRY_ATTEMPTS:
            await asyncio.sleep(RETRY_DELAY_SECONDS)
            return await send_discord_reminder(bot, user_id, content, remind_at_ist, retry_count + 1)
        return False
    except Exception as e:
        logger.error(f"Error in send_discord_reminder: {e}")
        if retry_count < MAX_RETRY_ATTEMPTS:
            await asyncio.sleep(RETRY_DELAY_SECONDS)
            return await send_discord_reminder(bot, user_id, content, remind_at_ist, retry_count + 1)
        return False

async def check_reminders_periodically():
    """Check for due reminders and send them periodically."""
    reminder_check_interval = 5  # seconds
    consecutive_errors = 0
    max_consecutive_errors = 10
    backoff_multiplier = 1.5
    
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
                            # Single-user mode: always send to the owner
                            # Convert UTC to IST for user-facing message
                            from zoneinfo import ZoneInfo
                            remind_at = reminder.remind_at
                            if remind_at.tzinfo is None:
                                remind_at = remind_at.replace(tzinfo=ZoneInfo("UTC"))
                            else:
                                remind_at = remind_at.astimezone(ZoneInfo("UTC"))
                            remind_at_ist = remind_at.astimezone(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Use the enhanced method to send reminders
                            success = await send_discord_reminder(
                                DISCORD_BOT_INSTANCE, 
                                OWNER_USER_ID, 
                                reminder.content, 
                                remind_at_ist
                            )
                            
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
                                    # Custom recurrence handling would go here
                                    pass
                                
                                if next_time:
                                    reminder.remind_at = next_time
                                    reminder.is_sent = False
                                    await db.commit()
                                else:
                                    reminder.is_sent = True
                                    await db.commit()
                            else:
                                reminder.is_sent = True
                                await db.commit()
                        except Exception as e:
                            logger.error(f"Error sending reminder {reminder.id}: {e}")
            
            # Reset error counter on success
            consecutive_errors = 0
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in reminder checking loop: {e}")
            
            # If we've had too many consecutive errors, increase the delay
            if consecutive_errors > max_consecutive_errors:
                error_wait = reminder_check_interval * (backoff_multiplier ** (consecutive_errors - max_consecutive_errors))
                error_wait = min(error_wait, 300)  # Cap at 5 minutes
                await asyncio.sleep(error_wait)
        
        # Wait before checking again
        await asyncio.sleep(reminder_check_interval)