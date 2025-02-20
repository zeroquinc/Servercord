from src.discord.embed import EmbedBuilder
from api.trakt.client import TraktClient
from utils.datetime import TimeCalculator

from config.globals import TRAKT_ICON

from utils.custom_logger import logger

# Function to process recent ratings and send them to a specified Discord channel as embeds
async def process_ratings(ratings_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, then = TimeCalculator.get_time_ago(hours=1)
    ratings = sorted(user.get_ratings(start_time=then, end_time=now), key=lambda rating: rating.date)

    async def process_rating(rating):
        author_formats = {
            'show': "Trakt: A show has been rated",
            'season': "Trakt: A season has been rated",
            'episode': "Trakt: An episode has been rated",
            'movie': "Trakt: A movie has been rated"
        }
        title_formats = {
            'show': f"{rating.show_title}",
            'season': f"{rating.show_title} - Season {rating.season_id}",
            'episode': f"{rating.show_title} - S{rating.season_id}E{rating.episode_id}",
            'movie': f"{rating.title} ({rating.year})"
        }
        author = author_formats[rating.type]
        title = title_formats[rating.type]
        embed_builder = EmbedBuilder(title=title, color=0xFF0000, url=rating.url)
        embed_builder.add_field(name="User", value=f"[{username}](https://trakt.tv/users/{username})", inline=True)
        embed_builder.add_field(name="Rating", value=f"{rating.rated} :star:", inline=True)
        embed_builder.set_thumbnail(url=rating.poster)
        embed_builder.set_author(name=author, icon_url=TRAKT_ICON)

        logger.info(f"Sending rating embed to Discord: {title}")

        await embed_builder.send_embed(ratings_channel)

    for rating in ratings:
        await process_rating(rating)