from datetime import datetime, timedelta
from api.trakt.client import TraktClient

client = TraktClient()
user = client.user('desiler')

# Get the current time and the time one hour ago
now = datetime.now()
one_hour_ago = now - timedelta(hours=1200)

#ratings = user.get_ratings(start_time=one_hour_ago, end_time=now)
#ratings = user.get_ratings()
#for rating in ratings:
favorites = user.get_favorites(start_time=one_hour_ago, end_time=now)
for favorite in favorites:
    print(f"Title: {favorite.title}")
    print(f"Media type: {favorite.type}")
    print(f"Season: {favorite.season_id}")
    print(f"Episode: {favorite.episode_id}")
    print(f"Listed at: {favorite.listed_at}")
    print(f"Show title: {favorite.show_title}")
    print()