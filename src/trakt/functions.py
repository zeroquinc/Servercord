from datetime import datetime, timedelta

from src.discord.embed import EmbedBuilder
from api.trakt.client import TraktClient

async def process_ratings(ratings_channel, username):
    client = TraktClient()
    user = client.user(username)
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=30)
    ratings = user.get_ratings(start_time=one_hour_ago, end_time=now)

    for rating in ratings:
        description = f"**{rating.show_title} (S{rating.season_id}E{rating.episode_id})**\n{rating.title}\n\n {username} rated {rating.rated} :star:"
        embed_builder = EmbedBuilder(description=description, color=0xFF0000)
        embed_builder.set_footer(text=rating.date)
        embed_builder.set_thumbnail(url=rating.poster)
        await embed_builder.send_embed(ratings_channel)