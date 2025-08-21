import threading
import asyncio
import os
from app.discord_bot.bot import run_bot
from app.reminders import DISCORD_BOT_INSTANCE, check_reminders_periodically, register_bot_instance

_bot_started = False
_reminder_task = None

def start_discord_bot(loop: asyncio.AbstractEventLoop):
    """Starts the discord bot in a new thread."""
    global _bot_started, _reminder_task
    
    if _bot_started:
        return
        
    _bot_started = True
    
    # Start the reminder checking task silently
    if not _reminder_task:
        _reminder_task = loop.create_task(check_reminders_periodically())
    
    # A simple event to wait until the bot is ready
    bot_ready_event = threading.Event()

    def target_with_bot_instance():
        # This function runs in the new thread
        def on_bot_ready(bot_instance):
            # This callback is used to pass the bot instance back to the main thread
            if bot_instance:
                register_bot_instance(bot_instance)
            bot_ready_event.set()

        try:
            run_bot(loop, on_bot_ready)
        except Exception:
            # Silent failure
            bot_ready_event.set()

    thread = threading.Thread(target=target_with_bot_instance, daemon=True)
    thread.start()
    
    # Wait for the bot to be ready before the main application continues
    bot_ready_event.wait()