import asyncio
import concurrent.futures
import logging
from datetime import datetime
import discord
from app.core.llm import ask_llm
from sqlalchemy import select
from app.db.models import Reminder, SessionLocal, User
import traceback
from app.core.time_utils import get_current_time_utc, get_current_time, format_time

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
                        # Format the time for display
                        formatted_time = remind_at_ist
                        
                        # Check if this is a short duration reminder (for the LLM and fallback messages)
                        now_ist = format_time(get_current_time(timezone="Asia/Kolkata"), include_timezone=False)
                        is_short_duration = (formatted_time == now_ist or 
                                           "second" in formatted_time.lower() or 
                                           "minute" in formatted_time.lower() and "1 minute" in formatted_time.lower())
                        
                        # Try to get a personalized reminder message using LLM
                        try:
                            from app.core.llm import ask_llm
                            
                            prompt = f"""
                            Generate a personalized reminder message for a user.
                            
                            Reminder details:
                            - Task: {content}
                            - {"This is an immediate reminder that you just set moments ago." if is_short_duration else f"Scheduled time: {formatted_time}"}
                            
                            Make it conversational, friendly and helpful. Address the user as "Sir".
                            Format the message with Markdown - make the reminder content stand out with bold or emoji.
                            Keep it concise (under 100 words) but make it warm and personal.
                            
                            Example format for immediate reminders:
                            **Time for [task]!** 🔔
                            
                            [Brief friendly and helpful note about the task]
                            
                            Example format for scheduled reminders:
                            **Reminder:** [task] ⏰
                            
                            [Brief friendly note including the scheduled time]
                            """
                            
                            messages_for_llm = [{"role": "user", "content": prompt}]
                            personalized_message = await ask_llm(messages_for_llm)
                            
                            # Use LLM message if it looks good
                            if 30 < len(personalized_message) < 300 and "Sir" in personalized_message:
                                await discord_user.send(personalized_message)
                                return True
                            
                        except Exception as e:
                            logger.warning(f"Error generating personalized reminder message: {e}")
                            # Fall back to default message
                        
                        # Default message as fallback
                        if is_short_duration:
                            message = f"Hello Sir! 🔔\n\n**It's time to {content}!**\n\nYour immediate reminder is now active. Hope this helps you stay on track!"
                        else:
                            message = f"Hello Sir! ⏰\n\n**Reminder: {content}**\n\nThis reminder was scheduled for {formatted_time}. I hope this helps with your planning!"
                        
                        await discord_user.send(message)
                        return True
                    else:
                        logger.warning(f"Could not fetch Discord user with ID {user_id}")
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
            logger.warning("Bot instance not available or missing event loop")
            return False
    except concurrent.futures.TimeoutError:
        if retry_count < MAX_RETRY_ATTEMPTS:
            logger.warning(f"Timeout sending reminder, retrying ({retry_count+1}/{MAX_RETRY_ATTEMPTS})")
            await asyncio.sleep(RETRY_DELAY_SECONDS)
            return await send_discord_reminder(bot, user_id, content, remind_at_ist, retry_count + 1)
        logger.error(f"Failed to send reminder after {MAX_RETRY_ATTEMPTS} attempts")
        return False
    except Exception as e:
        logger.error(f"Error in send_discord_reminder: {e}")
        if retry_count < MAX_RETRY_ATTEMPTS:
            await asyncio.sleep(RETRY_DELAY_SECONDS)
            return await send_discord_reminder(bot, user_id, content, remind_at_ist, retry_count + 1)
        return False

async def check_reminders_periodically():
    """Check for due reminders and send them periodically."""
    reminder_check_interval = 1  # Reduced to 1 second to better handle short duration reminders
    consecutive_errors = 0
    max_consecutive_errors = 10
    backoff_multiplier = 1.5
    
    # Start the time synchronization task to ensure accurate time
    from app.core.time_utils import start_time_sync_task
    # Run as a separate task to avoid blocking the reminder checker
    sync_task = asyncio.create_task(start_time_sync_task())
    
    # Ensure we have synchronized time before checking reminders
    # Wait for initial time sync to complete (max 10 seconds)
    try:
        from app.core.time_utils import sync_time
        await asyncio.wait_for(sync_time(), timeout=10)
        print("Time synchronization completed successfully")
    except asyncio.TimeoutError:
        print("Initial time sync timed out, will retry in background")
    except Exception as e:
        print(f"Error during initial time sync: {e}")
    
    while True:
        try:
            # Use synchronized time from NTP servers
            now = get_current_time_utc()
            
            # Convert to naive datetime for PostgreSQL comparison
            # This is necessary because PostgreSQL TIMESTAMP WITHOUT TIME ZONE cannot
            # be directly compared with timezone-aware datetimes
            now_naive = now.replace(tzinfo=None)
            
            async with SessionLocal() as db:
                result = await db.execute(
                    select(Reminder).where(
                        Reminder.remind_at <= now_naive,
                        Reminder.is_sent == False
                    )
                )
                due_reminders = result.scalars().all()
                
                if due_reminders and DISCORD_BOT_INSTANCE:
                    from dateutil.relativedelta import relativedelta
                    from zoneinfo import ZoneInfo
                    for reminder in due_reminders:
                        try:
                            # Single-user mode: always send to the owner
                            # Convert naive UTC to timezone-aware UTC first
                            from app.core.time_utils import get_timezone_object
                            remind_at = reminder.remind_at
                            
                            
                            # Ensure the time has timezone info (naive->aware conversion)
                            if remind_at.tzinfo is None:
                                remind_at = remind_at.replace(tzinfo=ZoneInfo("UTC"))
                            
                            # Convert to IST for user display
                            remind_at_ist = remind_at.astimezone(ZoneInfo("Asia/Kolkata"))
                            
                            # Format reminder time for display
                            formatted_time = format_time(remind_at_ist, include_timezone=False)
                            
                            # Send the reminder
                            await send_discord_reminder(DISCORD_BOT_INSTANCE, OWNER_USER_ID, reminder.content, formatted_time)
                            success = await send_discord_reminder(
                                DISCORD_BOT_INSTANCE, 
                                OWNER_USER_ID, 
                                reminder.content, 
                                formatted_time
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
                                elif reminder.recurrence == "yearly":
                                    next_time = reminder.remind_at + relativedelta(years=1)
                                elif reminder.recurrence_rule:
                                    # Custom recurrence handling would go here
                                    # For more complex recurrences, parse and apply the rule
                                    if isinstance(reminder.recurrence_rule, dict):
                                        rule = reminder.recurrence_rule
                                        if rule.get("type") == "weekday":
                                            # Every weekday (Monday-Friday)
                                            next_time = reminder.remind_at + relativedelta(days=1)
                                            while next_time.weekday() >= 5:  # Skip weekend
                                                next_time += relativedelta(days=1)
                                        elif rule.get("type") == "weekend":
                                            # Every weekend day (Saturday-Sunday)
                                            next_time = reminder.remind_at + relativedelta(days=1)
                                            while next_time.weekday() < 5:  # Skip weekdays
                                                next_time += relativedelta(days=1)
                                        elif rule.get("interval"):
                                            # Custom interval
                                            interval = rule.get("interval", 1)
                                            unit = rule.get("unit", "days")
                                            if unit == "days":
                                                next_time = reminder.remind_at + relativedelta(days=interval)
                                            elif unit == "weeks":
                                                next_time = reminder.remind_at + relativedelta(weeks=interval)
                                            elif unit == "months":
                                                next_time = reminder.remind_at + relativedelta(months=interval)
                                            elif unit == "hours":
                                                next_time = reminder.remind_at + relativedelta(hours=interval)
                                
                                if next_time:
                                    # Make sure next_time is stored as naive UTC
                                    if next_time.tzinfo is not None:
                                        next_time = next_time.replace(tzinfo=None)
                                    reminder.remind_at = next_time
                                    reminder.is_sent = False
                                    logger.info(f"Scheduled next occurrence of recurring reminder '{reminder.content}' for {next_time}")
                                    await db.commit()
                                else:
                                    reminder.is_sent = True
                                    await db.commit()
                            else:
                                reminder.is_sent = True
                                await db.commit()
                        except Exception as e:
                            logger.error(f"Error sending reminder {reminder.id}: {e}")
                            logger.error(traceback.format_exc())
            
            # Reset error counter on success
            consecutive_errors = 0
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in reminder checking loop: {e}")
            logger.error(traceback.format_exc())
            
            # If we've had too many consecutive errors, increase the delay
            if consecutive_errors > max_consecutive_errors:
                error_wait = reminder_check_interval * (backoff_multiplier ** (consecutive_errors - max_consecutive_errors))
                error_wait = min(error_wait, 300)  # Cap at 5 minutes
                logger.warning(f"Too many consecutive errors, backing off for {error_wait} seconds")
                await asyncio.sleep(error_wait)
        
        # Wait before checking again
        await asyncio.sleep(reminder_check_interval)