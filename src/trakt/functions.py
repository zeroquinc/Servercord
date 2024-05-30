from src.discord.embed import EmbedBuilder
from api.trakt.client import TraktClient
from utils.datetime import TimeCalculator

from config.globals import TRAKT_ICON

# Function to process recent ratings and send them to a specified Discord channel as embeds
async def process_ratings(ratings_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, then = TimeCalculator.get_time_ago(hours=1)
    ratings = sorted(user.get_ratings(start_time=then, end_time=now), key=lambda rating: rating.date)

    async def process_rating(rating):
        description_formats = {
            'show': f"{username} rated this {rating.type} {rating.rated} :star:",
            'season': f"{username} rated this {rating.type} {rating.rated} :star:",
            'episode': f"{username} rated this {rating.type} {rating.rated} :star:",
            'movie': f"{username} rated this {rating.type} {rating.rated} :star:"
        }
        author_formats = {
            'show': "A show has been rated on Trakt",
            'season': "A season has been rated on Trakt",
            'episode': "An episode has been rated on Trakt",
            'movie': "A movie has been rated on Trakt"
        }
        title_formats = {
            'show': f"{rating.show_title}",
            'season': f"{rating.show_title} - Season {rating.season_id}",
            'episode': f"{rating.show_title} - S{rating.season_id}E{rating.episode_id}",
            'movie': f"{rating.title} ({rating.year})"
        }
        description = description_formats[rating.type]
        author = author_formats[rating.type]
        title = title_formats[rating.type]
        embed_builder = EmbedBuilder(title=title, description=description, color=0xFF0000)
        embed_builder.set_thumbnail(url=rating.poster)
        embed_builder.set_author(name=author, icon_url=TRAKT_ICON)
        await embed_builder.send_embed(ratings_channel)

    for rating in ratings:
        await process_rating(rating)
        
# Function to process recent favorites and send them to a specified Discord channel as embeds
async def process_favorites(favorites_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, then = TimeCalculator.get_time_ago(hours=24)
    favorites = sorted(user.get_favorites(start_time=then, end_time=now), key=lambda favorite: favorite.date)

    async def process_favorite(favorite):
        description_formats = {
            'show': f"{username} favorited this {favorite.type}",
            'season': f"{username} favorited this {favorite.type}",
            'episode': f"{username} favorited this {favorite.type}",
            'movie': f"{username} favorited this {favorite.type}"
        }
        author_formats = {
            'show': "A show has been favorited on Trakt",
            'season': "A season has been favorited on Trakt",
            'episode': "An episode has been favorited on Trakt",
            'movie': "A movie has been favorited on Trakt"
        }
        title_formats = {
            'show': f"{favorite.show_title}",
            'season': f"{favorite.show_title} - Season {favorite.season_id}",
            'episode': f"{favorite.show_title} - S{favorite.season_id}E{favorite.episode_id}",
            'movie': f"{favorite.title} ({favorite.year})"
        }
        description = description_formats[favorite.type]
        author = author_formats[favorite.type]
        title = title_formats[favorite.type]
        embed_builder = EmbedBuilder(title=title, description=description, color=0xFF0000)
        embed_builder.set_thumbnail(url=favorite.poster)
        embed_builder.set_author(name=author, icon_url=TRAKT_ICON)
        await embed_builder.send_embed(favorites_channel)

    for favorite in favorites:
        await process_favorite(favorite)
