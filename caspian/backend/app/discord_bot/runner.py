import threading

from app.discord_bot.bot import run_bot


def start_discord_bot():
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
