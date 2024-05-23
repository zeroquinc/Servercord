import asyncio

from src.webhook.hook import HandleWebHook
from src.discord.bot import DiscordBot

from config.globals import DISCORD_TOKEN

if __name__ == "__main__":
    discord_bot = DiscordBot(DISCORD_TOKEN)
    webhook = HandleWebHook(discord_bot)

    loop = asyncio.get_event_loop()
    loop.create_task(webhook.start())
    loop.create_task(discord_bot.start())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(webhook.cleanup())