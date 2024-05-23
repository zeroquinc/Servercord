from datetime import datetime, timedelta
from api.trakt.client import TraktClient

client = TraktClient()
user = client.user('desiler')

# Get the current time and the time one hour ago
now = datetime.now()
one_hour_ago = now - timedelta(hours=1)

#ratings = user.get_ratings(start_time=one_hour_ago, end_time=now)
ratings = user.get_ratings()
for rating in ratings:
    print(f"Title: {rating.title}")
    print(f"Media type: {rating.type}")
    print(f"Season: {rating.season_id}")
    print(f"Episode: {rating.episode_id}")
    print(f"Rating: {rating.rated}")
    print(f"Rated at: {rating.rated_at}")
    print(f"Show title: {rating.show_title}")
    print()