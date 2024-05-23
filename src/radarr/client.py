import json
from utils.custom_logger import logger

class RadarrWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot

        # Global variables for the class to use in the embed creation
        self.event_type = self.payload.get('eventType', 'N/A')
        self.instance_name = self.payload.get('instanceName', 'N/A')
        self.old_version = self.payload.get('previousVersion', 'N/A')
        self.new_version = self.payload.get('newVersion', 'N/A')
        self.movie_title = self.payload.get('movie', {}).get('title', 'N/A')
        self.movie_year = self.payload.get('movie', {}).get('year', 'N/A')
        self.release_data = self.payload.get('release', {})
        self.quality = self.release_data.get('quality', 'N/A')
        self.size = self.release_data.get('size', 'N/A')
        self.indexer = self.release_data.get('indexer', 'N/A')
        self.release_title = self.release_data.get('releaseTitle', 'N/A')
        self.custom_format_score = self.release_data.get('customFormatScore', 'N/A')
        self.custom_formats = self.release_data.get('customFormats', [])
        self.tmdb_id = self.payload.get('movie', {}).get('tmdbId', 'N/A')
        self.embed_title = f"{self.movie_title} ({self.movie_year})"

    async def handle_webhook(self):
        logger.info(f"Processing Radarr webhook payload for event type: {self.payload.get('eventType')}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")