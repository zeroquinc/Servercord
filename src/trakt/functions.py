from utils.datetime import get_times

from src.discord.embed import EmbedBuilder
from api.trakt.client import TraktClient

async def process_ratings(ratings_channel, username):
    client = TraktClient()
    user = client.user(username)
    now, one_hour_ago = get_times()
    ratings = user.get_ratings(start_time=one_hour_ago, end_time=now)

    async def process_rating(rating):
        description_formats = {
            'show': f"**{rating.show_title}**\n{rating.title}\n\n {username} rated this {rating.type} with {rating.rated} :star:",
            'season': f"**{rating.show_title}**\nSeason {rating.season_id}\n\n {username} rated this {rating.type} with {rating.rated} :star:",
            'episode': f"**{rating.show_title} (S{rating.season_id}E{rating.episode_id})**\n{rating.title}\n\n {username} rated this {rating.type} with {rating.rated} :star:",
            'movie': f"**{rating.title} ({rating.year})**\n\n {username} rated this {rating.type} with {rating.rated} :star:"
        }
        description = description_formats[rating.type]
        embed_builder = EmbedBuilder(description=description, color=0xFF0000)
        embed_builder.set_footer(text=rating.date)
        embed_builder.set_thumbnail(url=rating.poster)
        await embed_builder.send_embed(ratings_channel)

    for rating in ratings:
        await process_rating(rating)
