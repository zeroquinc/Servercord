import asyncio

from webhook import HandleWebHook
from bot import DiscordBot

from config.globals import TOKEN

if __name__ == "__main__":
    discord_bot = DiscordBot(TOKEN)
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