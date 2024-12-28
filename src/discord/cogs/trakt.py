import discord
from discord.ext import commands
from src.trakt.global_weekly import create_weekly_global_embed
from utils.custom_logger import logger


class TraktCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trakt")
    async def trakt(self, ctx):
        """Fetches and displays the weekly global Trakt stats manually."""
        try:
            logger.info("!trakt command invoked")
            embed_data = create_weekly_global_embed()
            for embed in embed_data["embeds"]:
                await ctx.send(embed=discord.Embed.from_dict(embed))
        except Exception as e:
            logger.error(f"Error processing !trakt command: {e}")
            await ctx.send("An error occurred while fetching Trakt data.")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    logger.info('Trakt cog have been loaded')
    await bot.add_cog(TraktCog(bot))