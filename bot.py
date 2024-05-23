import discord
from discord.ext import commands, tasks

from config.config import DELAY_START

from utils.custom_logger import logger

class DiscordBot:
    def __init__(self, token):
        self.token = token
        self.bot = commands.Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="127.0.0.1"
            )
        )

        # Register event listeners
        self.bot.add_listener(self.on_ready)

    ## Start the bot
    async def start(self):
        try:
            await self.bot.start(self.token)
        except Exception as e:
            logger.error(f"Error starting the bot: {e}")

    ## Event listener for when the bot is ready
    async def on_ready(self):
        logger.info(
            f'Logged in as {self.bot.user.name} ({self.bot.user.id}) and is ready!'
        )