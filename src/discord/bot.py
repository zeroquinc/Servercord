import discord
from discord.ext import commands

from utils.custom_logger import logger

class DiscordBot:
    def __init__(self, token):
        intents = discord.Intents.default()
        intents.message_content = True

        self.token = token
        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents,
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
        
        # Load the tasks cog
        logger.info('Loading tasks cog')
        await self.bot.load_extension('src.discord.cogs.tasks')
        
        # Load commands here

    ## Post an single embed to a channel
    async def dispatch_embed(self, channel_id, embed):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found")
            return
        try:
            await channel.send(embed=embed)
            logger.info(f"Embed dispatched with title: {embed.title} and author: {embed.author.name}")
        except Exception as e:
            logger.error(f"Error dispatching embed: {e}")