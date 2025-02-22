import json
from utils.custom_logger import logger

from src.tmdb.client import TMDb
from src.radarr.functions import process_webhook
from config.globals import RADARR_CHANNEL, UPDATE_CHANNEL

class RadarrWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.initialize_global_variables()

    def initialize_global_variables(self):
        self.event_type = self.payload.get('eventType', 'N/A')
        self.instance_name = self.payload.get('instanceName', 'N/A')
        self.old_version = self.payload.get('previousVersion', 'N/A')
        self.new_version = self.payload.get('newVersion', 'N/A')
        self.movie = self.payload.get('movie', {})
        self.movie_title = self.movie.get('title', 'N/A')
        self.movie_year = self.movie.get('year', 'N/A')
        self.release_data = self.payload.get('release', {})
        self.quality = self.release_data.get('quality', 'N/A')
        self.size = self.release_data.get('size', 'N/A')
        self.indexer = self.release_data.get('indexer', 'N/A')
        self.release_title = self.release_data.get('releaseTitle', 'N/A')
        self.custom_format_score = self.release_data.get('customFormatScore', 'N/A')
        self.custom_formats = self.release_data.get('customFormats', [])
        self.tmdb_id = self.movie.get('tmdbId', 'N/A')
        self.embed_title = f"{self.movie_title} ({self.movie_year})"
        if self.event_type != 'Test':
            self.poster = TMDb.movie_poster_path(self.tmdb_id)

    async def handle_webhook(self):
        logger.info(f"Processing Radarr webhook payload for event type: {self.event_type}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")

        # Check if the event is "ApplicationUpdate" and set the channel accordingly
        if self.event_type == 'ApplicationUpdate':
            channel = self.discord_bot.bot.get_channel(UPDATE_CHANNEL)  # Send to the update channel
        else:
            channel = self.discord_bot.bot.get_channel(RADARR_CHANNEL)  # Send to the default Radarr channel

        await process_webhook(self, channel)