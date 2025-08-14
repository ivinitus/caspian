
import os
import discord
import asyncio
from app.core.llm import ask_openai
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

class CaspianBot(discord.Client):
    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.typing()
            response = await ask_openai([
                {"role": "user", "content": message.content}
            ])
            reply = response['choices'][0]['message']['content']
            await message.channel.send(f"Sir, {reply}")

def run_bot():
    intents = discord.Intents.default()
    client = CaspianBot(intents=intents)
    client.run(DISCORD_TOKEN)
