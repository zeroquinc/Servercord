from src.discord.embed import EmbedBuilder
from src.trakt.client import TraktClient
from utils.datetime import TimeCalculator

from config.globals import TRAKT_ICON

from utils.custom_logger import logger

# Function to process recent favorites and send them to a specified Discord channel as embeds
async def process_favorites(favorites_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, then = TimeCalculator.get_time_ago(hours=24)
    favorites = sorted(user.get_favorites(start_time=then, end_time=now), key=lambda favorite: favorite.date)

    async def process_favorite(favorite):
        author_formats = {
            'show': "Trakt: A show has been favorited",
            'season': "Trakt: A season has been favorited",
            'episode': "Trakt: An episode has been favorited",
            'movie': "Trakt: A movie has been favorited"
        }
        title_formats = {
            'show': f"{favorite.show_title}",
            'season': f"{favorite.show_title} - Season {favorite.season_id}",
            'episode': f"{favorite.show_title} - S{favorite.season_id}E{favorite.episode_id}",
            'movie': f"{favorite.title} ({favorite.year})"
        }
        author = author_formats[favorite.type]
        title = title_formats[favorite.type]
        embed_builder = EmbedBuilder(title=title, color=0xFF0000, url=favorite.url)
        embed_builder.add_field(name="User", value=f"[{username}](https://trakt.tv/users/{username})", inline=True)
        embed_builder.set_thumbnail(url=favorite.poster)
        embed_builder.set_author(name=author, icon_url=TRAKT_ICON)

        logger.info(f"Sending favorite embed to Discord: {title}")

        await embed_builder.send_embed(favorites_channel)

    for favorite in favorites:
        await process_favorite(favorite)
