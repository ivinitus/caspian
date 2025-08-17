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

            # Lazy import to avoid circular imports
            from app.core.llm import ask_llm

            try:
                text = await ask_llm([
                    {
                        "role": "system",
                        "content": (
                            "You are Caspian, a witty and loyal AI butler. "
                            "You always address the user as 'Sir' — never 'Madam' or 'Sir/Madam'. "
                            "Your tone is respectful, charming, and consistent."
                        )
                    },
                    {"role": "user", "content": message.content}
                ])
                text = text.replace("Sir/Madam", "Sir").replace("Madam", "Sir")
                await message.channel.send(text)
            except Exception as e:
                await message.channel.send("Apologies, I encountered an error while processing your request.")
                print(f"Error in on_message: {e}")


def run_bot():
    token = settings.discord_token
    if not token:
        print("DISCORD_TOKEN not set; Discord bot will not start.")
        return

    intents = discord.Intents.default()
    intents.message_content = True

    client = CaspianBot(intents=intents)
    client.run(token)
