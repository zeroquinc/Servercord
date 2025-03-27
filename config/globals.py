from dotenv import load_dotenv
import os

load_dotenv()

# Discord
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_THUMBNAIL = "https://i.postimg.cc/KvSTwcQ0/undefined-Imgur.png"

# Plex
PLEX_PLAYING = int(os.getenv("PLEX_PLAYING"))
PLEX_CONTENT = int(os.getenv("PLEX_CONTENT"))
PLEX_ICON = "https://i.imgur.com/ZuFghbX.png"

# TMDB
TMDB_API_KEY = os.getenv("TMDB_API_KEY")