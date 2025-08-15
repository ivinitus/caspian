
import discord

from app.core.config import settings


class CaspianBot(discord.Client):
    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.typing()
            # Lazy import to avoid circulars
            from app.core.llm import ask_openai

            response = await ask_openai([
                {"role": "user", "content": message.content}
            ])
            reply = response['choices'][0]['message']['content']
            await message.channel.send(f"Sir, {reply}")


def run_bot():
    token = settings.discord_token
    if not token:
        print("DISCORD_TOKEN not set; Discord bot will not start.")
        return

    intents = discord.Intents.default()
    client = CaspianBot(intents=intents)
    client.run(token)
