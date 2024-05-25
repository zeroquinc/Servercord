import json
from utils.custom_logger import logger

from src.radarr.functions import process_webhook

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

    async def handle_webhook(self):
        logger.info(f"Processing Radarr webhook payload for event type: {self.event_type}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")
        channel = self.discord_bot.bot.get_channel(1052967176828616724)
        await process_webhook(self, channel)