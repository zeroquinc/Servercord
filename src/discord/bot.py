import discord
from discord.ext import commands, tasks

from config.config import DELAY_START

from utils.custom_logger import logger
from utils.datetime import get_times
from src.discord.embed import EmbedBuilder
from api.trakt.client import TraktClient

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

        @self.bot.command()
        async def favorite(ctx, username: str = None):
            if username is None:
                await ctx.send('No username given!')
                return

            logger.info(f'Trakt command invoked with username: {username}')
            client = TraktClient()
            user = client.user(username)
            # Get the current time and the time one hour ago
            now, one_hour_ago = get_times()
            favorites = user.get_favorites(start_time=one_hour_ago, end_time=now)
            # Add the last favorite to the embed
            if favorites:
                latest_favorite = favorites[-1]
                # Create an EmbedBuilder instance
                embed_builder = EmbedBuilder(description=f'{username} has favorited {latest_favorite.title}')
            else:
                embed_builder = EmbedBuilder(description=f'{username} has no favorites')
            # Send the embed to the channel where the command was invoked
            await embed_builder.send_embed(ctx.channel)
            
        @self.bot.command()
        async def rating(ctx, username: str = None):
            if username is None:
                await ctx.send('No username given!')
                return

            logger.info(f'Trakt command invoked with username: {username}')
            client = TraktClient()
            user = client.user(username)
            # Get the current time and the time one hour ago
            now, one_hour_ago = get_times()
            ratings = user.get_ratings(start_time=one_hour_ago, end_time=now)
            # Add the last favorite to the embed
            if ratings:
                latest_rating = ratings[-1]
                # Create an EmbedBuilder instance
                embed_builder = EmbedBuilder(description=f'{username} has rated "**{latest_rating.title}**"\n{latest_rating.rated_at} with a score of {latest_rating.rated}')
                embed_builder.set_footer(text=f"Media type: {latest_rating.type}")
            else:
                embed_builder = EmbedBuilder(description=f'{username} has no ratings')
            # Send the embed to the channel where the command was invoked
            await embed_builder.send_embed(ctx.channel)