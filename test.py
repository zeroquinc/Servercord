from api.trakt.client import TraktClient

client = TraktClient()
shows_instance = client.shows()

for show in shows_instance.get_trending():
    print(show.title)
    
for show in shows_instance.get_popular():
    print(show.title)