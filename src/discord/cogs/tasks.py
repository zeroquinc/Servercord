from discord.ext import tasks, commands
import asyncio
from datetime import timedelta

from utils.custom_logger import logger
from utils.datetime import TimeCalculator
from src.trakt.functions import process_ratings, process_favorites
from config.globals import TRAKT_CHANNEL, TRAKT_USERNAME, ENABLE_DELAY, DISCORD_SERVER_ID

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.trakt_ratings.start()
        self.trakt_favorites.start()

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
            
    @tasks.loop(hours=12)
    async def update_disk_space_channel(self):
        await self.bot.wait_until_ready()
        space = self.get_disk_space()
        guild_id = DISCORD_SERVER_ID
        guild = self.bot.get_guild(guild_id)

        if guild is not None:
            # Check for any channel with "Disk Space" in its name
            disk_space_channel = next((channel for channel in guild.channels if "Disk Space" in channel.name), None)

            if disk_space_channel is not None:
                # If a "Disk Space" channel exists, update its name
                await disk_space_channel.edit(name=space)
            else:
                # If no "Disk Space" channel exists, create a new voice channel
                await guild.create_voice_channel(name=space)
        else:
            print(f"Guild with ID {guild_id} not found.")

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