import discord
from discord.ext import commands
from discord import app_commands
from src.trakt.global_weekly import create_weekly_global_embed
from utils.custom_logger import logger

class TraktCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="trakt", description="Fetches and displays the weekly global Trakt stats.")
    async def trakt(self, interaction: discord.Interaction):
        """Fetches and displays the weekly global Trakt stats manually."""
        await interaction.response.defer()  # Defers the interaction to avoid timeout

        try:
            logger.info("/trakt command invoked")
            embed_data = create_weekly_global_embed()

            # Sending the first embed
            embeds = [discord.Embed.from_dict(embed) for embed in embed_data["embeds"]]

            if embeds:
                await interaction.followup.send(embeds=embeds)
            else:
                await interaction.followup.send("No data available.", ephemeral=True)

        except Exception as e:
            logger.error(f"Error processing /trakt command: {e}")
            await interaction.followup.send("An error occurred while fetching Trakt data.", ephemeral=True)

async def setup(bot):
    """Setup function to add the cog to the bot."""
    logger.info('Trakt cog has been loaded')
    await bot.add_cog(TraktCog(bot))