from dotenv import load_dotenv
import os

# DotEnv
load_dotenv()

# Discord Globals
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
TOKEN = os.environ["DISCORD_TOKEN"]

# Trakt
TRAKT_USERNAME = "desileR"
TRAKT_CLIENTID = os.getenv("TRAKT_CLIENTID")

# API Keys
TMDB_API_KEY = os.getenv("TMDB_API_KEY")