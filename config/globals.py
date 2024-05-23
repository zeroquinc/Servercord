from dotenv import load_dotenv
import os

load_dotenv()

# Discord
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

# Trakt
TRAKT_API_URL = "https://api.trakt.tv"
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENTID")

# TMDB
TMDB_API_KEY = os.getenv("TMDB_API_KEY")