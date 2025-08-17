import threading
import asyncio
from app.discord_bot.bot import run_bot
from app.reminders import DISCORD_BOT_INSTANCE

def start_discord_bot(loop: asyncio.AbstractEventLoop):
    """Starts the discord bot in a new thread."""
    
    # A simple event to wait until the bot is ready
    bot_ready_event = threading.Event()

    def target_with_bot_instance():
        # This function runs in the new thread
        def on_bot_ready(bot_instance):
            # This callback is used to pass the bot instance back to the main thread
            global DISCORD_BOT_INSTANCE
            DISCORD_BOT_INSTANCE = bot_instance
            bot_ready_event.set()

        run_bot(loop, on_bot_ready)

    thread = threading.Thread(target=target_with_bot_instance, daemon=True)
    thread.start()
    
    # Wait for the bot to be ready before the main application continues
    print("Waiting for Discord bot to be ready...")
    bot_ready_event.wait()
    print("Discord bot is ready.")