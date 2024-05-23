Trakt Client Example with Ratings and Favorites
================================================

**Importing Necessary Modules**

```python
from datetime import datetime, timedelta
from api.trakt.client import TraktClient
```

**Initializing the Client and User**

```python
client = TraktClient()
user = client.user('username')
```

**Setting Up Time Variables**

This example sets up two time variables: the current time (`now`) and the time 1 hour ago (`one_hour_ago`).

```python
# Get the current time and the time one hour ago
now = datetime.now()
one_hour_ago = now - timedelta(hours=1)
```

**Fetching Ratings**

start_time and end_time are optional!

```python
ratings = user.get_ratings(start_time=one_hour_ago, end_time=now)
ratings = user.get_ratings()
for rating in ratings:
    print(f"Title: {rating.title}")
    print(f"Media type: {rating.type}")
    print(f"Rating: {rating.rating}")
    print(f"Rated at: {rating.rated_at}")
    print()
```

**Fetching Favorites**

This example fetches and displays the user's favorite items within the specified time range.

favorites = user.get_favorites(start_time=one_hour_ago, end_time=now)
for favorite in favorites:
    print(f"Title: {favorite.title}")
    print(f"Media type: {favorite.type}")
    print(f"Season: {favorite.season_id}")
    print(f"Episode: {favorite.episode_id}")
    print(f"Listed at: {favorite.listed_at}")
    print(f"Show title: {favorite.show_title}")
    print()

Output Example
--------------

The output for favorites will look something like this:

```
Title: Lost City of Life
Media type: episode
Season: 02
Episode: 03
Rating: 10
Rated at: 2021-01-18 01:19:37+01:00
Show title: Cosmos
```

Notes
-----

- Ensure that the `TraktClient` is correctly configured with your API credentials.

Feel free to modify the code according to your specific requirements.