from discord.ext import tasks, commands

from utils.custom_logger import logger
from src.trakt.functions import process_ratings, process_favorites

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.trakt_ratings.start()
        self.trakt_favorites.start()

    # Task to process recent Trakt ratings
    @tasks.loop(minutes=60)
    async def trakt_ratings(self):
        ratings_channel = self.bot.get_channel(1052967176828616724)
        try:
            await process_ratings(ratings_channel, 'desiler')
        except Exception as e:
            logger.error(f'Error processing recent Trakt ratings: {e}')
    
    # Task to process recent Trakt favorites
    @tasks.loop(hours=24)
    async def trakt_favorites(self):
        favorites_channel = self.bot.get_channel(1052967176828616724)
        try:
            await process_favorites(favorites_channel, 'desiler')
        except Exception as e:
            logger.error(f'Error processing recent Trakt ratings: {e}')

async def setup(bot):
    logger.info('Cogs have been loaded')
    await bot.add_cog(TasksCog(bot))