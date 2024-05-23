import asyncio

from src.webhook.hook import HandleWebHook
from src.discord.bot import DiscordBot

from config.globals import DISCORD_TOKEN

async def main():
    discord_bot = DiscordBot(DISCORD_TOKEN)
    webhook = HandleWebHook(discord_bot)

    await asyncio.gather(
        webhook.start(),
        discord_bot.start()
    )

    await webhook.cleanup()

if __name__ == "__main__":
    asyncio.run(main())