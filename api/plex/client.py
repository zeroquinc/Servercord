import json

from config.globals import PLEX_ICON, PLEX_PLAYING, PLEX_CONTENT
from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger

class PlexWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.extract_details()

    def extract_details(self):
        details = self.payload.get('source_metadata_details', {})
        stream_details = self.payload.get('stream_details', {})
        server_info = self.payload.get('server_info', {})
        fields = [
            'media_type', 'year', 'title', 'summary', 'quality', 'air_date', 'genres',
            'release_date', 'season_num00', 'episode_num00', 'episode_count', 'poster_url',
            'imdb_url', 'tvdb_url', 'trakt_url', 'plex_url', 'critic_rating', 'audience_rating',
            'rating', 'username', 'platform', 'player', 'product', 'video_decision',
            'remaining_time', 'duration_time', 'server_name', 'webhook_type'
        ]
        for field in fields:
            field_value = 'N/A'
            if field in details:
                field_value = details.get(field)
            elif field in stream_details:
                field_value = stream_details.get(field)
            elif field in server_info:
                field_value = server_info.get(field)
            setattr(self, field, field_value)

    async def handle_webhook(self):
        logger.info(f"Processing Plex webhook payload for event type: {self.webhook_type}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")
        await self.dispatch_embed()

    def determine_channel_id(self):
        channel_ids = {
            'nowplaying': PLEX_PLAYING,
            #'nowresuming': PLEX_PLAYING,
            #'finished': PLEX_PLAYING,
            'newcontent_episode': PLEX_CONTENT,
            'newcontent_season': PLEX_CONTENT,
            'newcontent_movie': PLEX_CONTENT,
        }
        return channel_ids.get(self.webhook_type, 'default_channel_id')

    def generate_embed(self):
        embed_creators = {
            'nowplaying': self.embed_for_event,
            #'nowresuming': self.embed_for_event,
            #'finished': self.embed_for_event,
            'newcontent_episode': self.embed_for_newcontent,
            'newcontent_season': self.embed_for_newcontent,
            'newcontent_movie': self.embed_for_newcontent,
        }
        return embed_creators.get(self.webhook_type)()

    def embed_for_event(self):
        title = f"{self.title} ({self.year})" if self.media_type == "movie" else f"{self.title} (S{self.season_num00}E{self.episode_num00})"
        embed = EmbedBuilder(title=title, url=self.plex_url, color=0xe5a00d)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        embed.set_author(name="Now Playing on Plex", icon_url=PLEX_ICON)
        embed.set_footer(text=f"{self.username.capitalize()} • {self.video_decision.title()} • {self.product}")
        return embed

    def embed_for_newcontent(self):
        embed = EmbedBuilder(title=self.get_newcontent_title(), description=self.get_description(), url=self.plex_url, color=0xe5a00d)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        if self.webhook_type == 'newcontent_season':
            embed.add_field(name="Episodes", value=f"{self.episode_count}", inline=True)
        if self.webhook_type == 'newcontent_movie':
            embed.set_footer(text=f"{self.genres}")
        embed.set_author(name=f"New {self.media_type.capitalize()} added to Plex", icon_url=PLEX_ICON)
        return embed

    def get_newcontent_title(self):
        titles = {
            'newcontent_episode': f"{self.title} (S{self.season_num00}E{self.episode_num00})",
            'newcontent_season': f"{self.title}",
            'newcontent_movie': f"{self.title} ({self.year})"
        }
        return titles.get(self.webhook_type, self.title)

    def get_description(self):
        descriptions = {
            'newcontent_episode': f"||{self.summary}||" if self.summary else '',
            'newcontent_season': f"||{self.summary}||" if self.summary else '',
            'newcontent_movie': f"||{self.summary}||" if self.summary else '' # We put || here because of how Discord handles spoilers
        }
        return descriptions.get(self.webhook_type, '')

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")