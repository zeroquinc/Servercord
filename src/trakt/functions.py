from src.discord.embed import EmbedBuilder
from api.trakt.client import TraktClient
from utils.datetime import get_times

# Function to process recent ratings and send them to a specified Discord channel as embeds
async def process_ratings(ratings_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, one_hour_ago = get_times()
    ratings = sorted(user.get_ratings(start_time=one_hour_ago, end_time=now), key=lambda rating: rating.date) # Get ratings sorted by date
    #ratings = user.get_ratings(start_time=one_hour_ago, end_time=now) # Get ratings

    async def process_rating(rating):
        description_formats = {
            'show': f"**{rating.title}**\n\n{username} rated this {rating.type}\n{rating.rated} :star:",
            'season': f"**{rating.show_title}**\nSeason {rating.season_id}\n\n{username} rated this {rating.type}\n{rating.rated} :star:",
            'episode': f"**{rating.show_title} (S{rating.season_id}E{rating.episode_id})**\n{rating.title}\n\n{username} rated this {rating.type}\n{rating.rated} :star:",
            'movie': f"**{rating.title} ({rating.year})**\n\n{username} rated this {rating.type}\n{rating.rated} :star:"
        }
        description = description_formats[rating.type]
        embed_builder = EmbedBuilder(description=description, color=0xFF0000)
        embed_builder.set_footer(text=rating.date)
        embed_builder.set_thumbnail(url=rating.poster)
        await embed_builder.send_embed(ratings_channel)

    for rating in ratings:
        await process_rating(rating)
        
# Function to process recent favorites and send them to a specified Discord channel as embeds
async def process_favorites(favorites_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, one_hour_ago = get_times()
    favorites = sorted(user.get_favorites(start_time=one_hour_ago, end_time=now), key=lambda favorite: favorite.date)

    async def process_favorite(favorite):
        description_formats = {
            'show': f"**{favorite.title}**\n\n{username} favorited this {favorite.type}",
            'season': f"**{favorite.show_title}**\nSeason {favorite.season_id}\n\n{username} favorited this {favorite.type}",
            'episode': f"**{favorite.show_title} (S{favorite.season_id}E{favorite.episode_id})**\n{favorite.title}\n\n{username} favorited this {favorite.type}",
            'movie': f"**{favorite.title} ({favorite.year})**\n\n{username} favorited this {favorite.type}"
        }
        description = description_formats[favorite.type]
        embed_builder = EmbedBuilder(description=description, color=0xFF0000)
        embed_builder.set_footer(text=favorite.date)
        embed_builder.set_thumbnail(url=favorite.poster)
        await embed_builder.send_embed(favorites_channel)

    for favorite in favorites:
        await process_favorite(favorite)
