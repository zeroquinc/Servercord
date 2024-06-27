import requests
from datetime import datetime, timedelta
from config.globals import TRAKT_CLIENT_ID, TMDB_API_KEY, TRAKT_ICON, DISCORD_THUMBNAIL
from utils.custom_logger import logger

# Constants
EMBED_COLORS = {'movie': 0xffa500, 'show': 0x67B7D1}
TMDB_URLS = {'movie': 'https://api.themoviedb.org/3/movie/', 'show': 'https://api.themoviedb.org/3/tv/'}
TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500/'
RANKING_EMOJIS = {1: ":first_place:", 2: ":second_place:", 3: ":third_place:"}

# Cache
image_cache = {}

def get_data_from_url(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return sorted(response.json(), key=lambda x: x['watcher_count'], reverse=True)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []

def fetch_image(item_type, item_id):
    if (image_url := image_cache.get((item_type, item_id))):
        return image_url

    url = f'{TMDB_URLS[item_type]}{item_id}?api_key={TMDB_API_KEY}&language=en-US'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if poster_path := data.get('poster_path'):
            image_url = f'{TMDB_IMAGE_URL}{poster_path}'
            image_cache[(item_type, item_id)] = image_url
            return image_url
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
    return ''

def create_embed(item_type, items, week, footer_text):
    embed = {
        "color": EMBED_COLORS[item_type],
        "fields": [],
        "thumbnail": {"url": ""},
        "image": {"url": DISCORD_THUMBNAIL},
        "author": {"name": f"Trakt - Top {item_type.capitalize()}s in Week {week}", "icon_url": TRAKT_ICON},
        "footer": {"text": footer_text}
    }

    for i, item in enumerate(items[:9]):
        image_url = fetch_image(item_type, item[item_type]['ids']['tmdb'])
        if not embed["thumbnail"]["url"] and image_url:
            embed["thumbnail"]["url"] = image_url
        embed["fields"].append({
            "name": f"{RANKING_EMOJIS.get(i + 1, '')} {item[item_type]['title']} ({item[item_type]['year']})",
            "value": f"[{item['watcher_count']:,} watchers](https://trakt.tv/{item_type}s/{item[item_type]['ids']['slug']})",
            "inline": True
        })
    return embed

def create_weekly_global_embed():
    headers = {'Content-Type': 'application/json', 'trakt-api-version': '2', "trakt-api-key": TRAKT_CLIENT_ID}
    _, previous_week_start, previous_week_end = datetime.now(), datetime.now() - timedelta(days=7), datetime.now() - timedelta(days=1)
    footer_text = f"{previous_week_start.strftime('%a %b %d %Y')} to {previous_week_end.strftime('%a %b %d %Y')}"
    week = previous_week_start.isocalendar()[1]

    movies = get_data_from_url('https://api.trakt.tv/movies/watched/period=weekly', headers)
    shows = get_data_from_url('https://api.trakt.tv/shows/watched/period=weekly', headers)

    movie_embed = create_embed('movie', movies, week, footer_text)
    show_embed = create_embed('show', shows, week, footer_text)

    logger.info("Created embed for global weekly event")
    return {"embeds": [movie_embed, show_embed]}