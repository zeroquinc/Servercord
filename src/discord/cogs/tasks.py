import discord
from discord.ext import tasks, commands
import asyncio
from datetime import timedelta

from utils.custom_logger import logger
from utils.datetime import TimeCalculator
from src.trakt.functions import process_ratings, process_favorites
from src.linux.disk_space import get_disk_space
from config.globals import TRAKT_CHANNEL, TRAKT_USERNAME, ENABLE_DELAY, DISCORD_SERVER_ID

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.trakt_ratings.start()
        self.trakt_favorites.start()
        self.update_disk_space_channel.start()

    # Task to process recent Trakt ratings
    @tasks.loop(minutes=60)
    async def trakt_ratings(self):
        ratings_channel = self.bot.get_channel(TRAKT_CHANNEL)
        try:
            await process_ratings(ratings_channel, TRAKT_USERNAME)
        except Exception as e:
            logger.error(f'Error processing recent Trakt ratings: {e}')

    # Task to process recent Trakt favorites
    @tasks.loop(hours=24)
    async def trakt_favorites(self):
        favorites_channel = self.bot.get_channel(TRAKT_CHANNEL)
        try:
            await process_favorites(favorites_channel, TRAKT_USERNAME)
        except Exception as e:
            logger.error(f'Error processing recent Trakt ratings: {e}')

    # Task to update the disk space channel
    @tasks.loop(hours=12)
    async def update_disk_space_channel(self):
        try:
            space = get_disk_space()
            guild_id = DISCORD_SERVER_ID
            guild = await self.bot.fetch_guild(guild_id)

            if guild is not None:
                # Look for a channel that starts with "HDD:"
                disk_space_channel = next((channel for channel in guild.channels if channel.name.startswith("HDD:")), None)

                if disk_space_channel is not None:
                    # Log found channel for debugging
                    logger.info(f"Found existing channel: {disk_space_channel.name}")
                    # Edit the existing channel
                    await disk_space_channel.edit(name=f"HDD: {space}")
                else:
                    # Log that no channel was found and a new one will be created
                    logger.info("No existing HDD: channel found, creating a new one.")
                    # Define the permission overwrite for @everyone role to disallow connect
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(connect=False)
                    }
                    # Create a new voice channel with the specified permissions
                    await guild.create_voice_channel(name=f"HDD: {space}", overwrites=overwrites)
            else:
                logger.info(f"Guild with ID {guild_id} not found.")
        except Exception as e:
            logger.error(f"Failed to update disk space channel: {e}")

    @trakt_ratings.before_loop
    async def before_trakt_ratings(self):
        if ENABLE_DELAY:
            seconds = TimeCalculator.seconds_until_next_hour()
            logger.info(f'Trakt ratings task will start in {str(timedelta(seconds=seconds))}')
            await asyncio.sleep(seconds)

    @trakt_favorites.before_loop
    async def before_trakt_favorites(self):
        if ENABLE_DELAY:
            seconds = TimeCalculator.seconds_until_next_day()
            logger.info(f'Trakt favorites task will start in {str(timedelta(seconds=seconds))}')
            await asyncio.sleep(seconds)

async def setup(bot):
    logger.info('Cogs have been loaded')
    await bot.add_cog(TasksCog(bot))