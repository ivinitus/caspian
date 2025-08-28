
import discord
from app.core.config import settings
from app.discord_bot.helpers import (
    detect_reminder_intent,
    handle_reminder_command,
    process_and_get_reply,
    handle_owner_commands,
    handle_dm_automation
)
import asyncio


class CaspianBot(discord.Client):
    def __init__(self, *args, **kwargs):
        self.main_loop = kwargs.pop('main_loop')
        self.on_ready_callback = kwargs.pop('on_ready_callback')
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        from app.reminders import register_bot_instance
        register_bot_instance(self)
        if self.on_ready_callback:
            self.on_ready_callback(self)

    async def on_message(self, message):
        if message.author == self.user:
            return
        # Owner/admin commands
        if await handle_owner_commands(self, message):
            return
        # DM automation commands
        if isinstance(message.channel, discord.DMChannel):
            if await handle_dm_automation(self, message):
                return
            reply = None
            # Only check for reminders if message starts with !remind
            if message.content.strip().lower().startswith('!remind'):
                reply = await handle_reminder_command(self, message)
            else:
                reply = await process_and_get_reply(self, message)
            if reply:
                await message.channel.send(reply)

def run_bot(main_loop, on_ready_callback):
    token = settings.discord_token
    if not token:
        if on_ready_callback:
            on_ready_callback(None)
        return
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        client = CaspianBot(intents=intents, main_loop=main_loop, on_ready_callback=on_ready_callback)
        client.run(token)
    except Exception as e:
        import logging
        logging.getLogger("discord_bot").error(f"Failed to start Discord bot: {e}")
        if on_ready_callback:
            on_ready_callback(None)