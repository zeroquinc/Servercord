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

# Trakt
TRAKT_API_URL = "https://api.trakt.tv"
TRAKT_ICON = "https://i.imgur.com/tvnkxAY.png"
TRAKT_CHANNEL = int(os.getenv("TRAKT_CHANNEL"))
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENTID")
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")

# TMDB
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Arrs
RADARR_CHANNEL = int(os.getenv("RADARR_CHANNEL"))
RADARR_ICON = "https://i.imgur.com/6U4aXO0.png"
SONARR_CHANNEL = int(os.getenv("SONARR_CHANNEL"))
SONARR_ICON = "https://i.imgur.com/dZSIKZE.png"
UPDATE_CHANNEL = int(os.getenv("UPDATE_CHANNEL"))

#  Jellyfin
JELLYFIN_PLAYING = int(os.getenv("JELLYFIN_PLAYING"))
JELLYFIN_CONTENT = int(os.getenv("JELLYFIN_CONTENT"))
JELLYFIN_ICON = "https://i.imgur.com/c5x6GjJ.png"

# Delay
ENABLE_DELAY = os.getenv("ENABLE_DELAY") == "True"