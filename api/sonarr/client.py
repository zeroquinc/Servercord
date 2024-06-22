import json
from utils.custom_logger import logger

from api.tmdb.client import TMDb
from src.sonarr.functions import process_webhook
from config.globals import SONARR_CHANNEL

class SonarrWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.initialize_global_variables()
        self.check_request_type()

    def initialize_global_variables(self):
        try:
            self.event_type = self.payload.get('eventType', 'N/A')
            self.instance_name = self.payload.get('instanceName', 'N/A')
            self.old_version = self.payload.get('previousVersion', 'N/A')
            self.new_version = self.payload.get('newVersion', 'N/A')
            self.series = self.payload.get('series', {})
            self.series_title = self.series.get('title', 'N/A')
            self.release_data = self.payload.get('release', {})
            self.episodes = self.payload.get('episodes', [])
            self.tvdb_id = self.series.get('tvdbId', 'N/A')
            self.quality = self.release_data.get('quality', 'N/A')
            self.size = self.release_data.get('size', 'N/A')
            self.indexer = self.release_data.get('indexer', 'N/A')
            self.release_title = self.release_data.get('releaseTitle', 'N/A')
            self.custom_format_score = self.release_data.get('customFormatScore', 'N/A')
            self.custom_formats = self.release_data.get('customFormats', [])
            self.episode_count = len(self.episodes)
            if self.event_type != 'Test' and self.tvdb_id != 'N/A':
                self.poster = TMDb.show_poster_path(self.tvdb_id)
        except Exception as e:
            logger.error(f"Error initializing global variables: {e}")

    def check_request_type(self):
        if self.episode_count > 1:
            self.handle_season_request()
        else:
            self.handle_episode_request()

    def handle_season_request(self):
        self.season_number = self.episodes[0].get('seasonNumber', 'N/A')
        self.formatted_season_number = f"{self.season_number:02d}"
        self.embed_title = f"{self.series_title} (Season {self.formatted_season_number})"

    def handle_episode_request(self):
        self.episode_title = self.episodes[0].get('title', 'N/A')
        self.episode_number = self.episodes[0].get('episodeNumber', 'N/A')
        self.season_number = self.episodes[0].get('seasonNumber', 'N/A')
        self.formatted_episode_number = f"{self.episode_number:02d}"
        self.formatted_season_number = f"{self.season_number:02d}"
        self.embed_title = f"{self.series_title} (S{self.formatted_season_number}E{self.formatted_episode_number})"

    async def handle_webhook(self):
        logger.info(f"Processing Sonarr webhook payload for event type: {self.event_type}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")
        channel = self.discord_bot.bot.get_channel(SONARR_CHANNEL)
        await process_webhook(self, channel)