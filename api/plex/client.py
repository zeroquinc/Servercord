import json
import discord

from config.globals import PLEX_ICON, PLEX_PLAYING, PLEX_CONTENT
from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger

class PlexWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot

        # Global variables for the class to use in the embed creation
        self.media_type = self.payload.get('source_metadata_details', {}).get('media_type', 'N/A').capitalize()
        self.year = self.payload.get('source_metadata_details', {}).get('year', 'N/A')
        self.title = self.payload.get('source_metadata_details', {}).get('title', 'N/A')
        self.summary = self.payload.get('source_metadata_details', {}).get('summary', 'N/A')
        self.quality = self.payload.get('source_metadata_details', {}).get('video_full_resolution', 'N/A')
        self.air_date = self.payload.get('source_metadata_details', {}).get('air_date', 'N/A')
        self.genres = self.payload.get('source_metadata_details', {}).get('genres', 'N/A')
        self.release_date = self.payload.get('source_metadata_details', {}).get('release_date', 'N/A')
        self.season_number = self.payload.get('source_metadata_details', {}).get('season_num00', 'N/A')
        self.episode_number = self.payload.get('source_metadata_details', {}).get('episode_num00', 'N/A')
        self.episode_count = self.payload.get('source_metadata_details', {}).get('episode_count', 'N/A')
        self.poster_url = self.payload.get('source_metadata_details', {}).get('poster_url', 'N/A')
        self.imdb_url = self.payload.get('source_metadata_details', {}).get('imdb_url', 'N/A')
        self.tvdb_url = self.payload.get('source_metadata_details', {}).get('thetvdb_url', 'N/A')
        self.trakt_url = self.payload.get('source_metadata_details', {}).get('trakt_url', 'N/A')
        self.critic_rating = self.payload.get('source_metadata_details', {}).get('critic_rating', 'N/A')
        self.audience_rating = self.payload.get('source_metadata_details', {}).get('audience_rating', 'N/A')
        self.rating = self.payload.get('source_metadata_details', {}).get('rating', 'N/A')
        self.username = self.payload.get('stream_details', {}).get('username', 'N/A')
        self.platform = self.payload.get('stream_details', {}).get('platform', 'N/A')
        self.player = self.payload.get('stream_details', {}).get('player', 'N/A')
        self.product = self.payload.get('stream_details', {}).get('product', 'N/A')
        self.video_decision = self.payload.get('stream_details', {}).get('video_decision', 'N/A').capitalize()
        self.remaining_time = self.payload.get('stream_details', {}).get('remaining_time', 'N/A')
        self.duration_time = self.payload.get('stream_details', {}).get('duration_time', 'N/A')
        self.server_name = self.payload.get('server_info', {}).get('server_name', 'N/A')
        self.webhook_type = self.payload.get('server_info', {}).get('webhook_type', 'N/A')

    async def handle_webhook(self):
        logger.info(f"Processing Plex webhook payload for event type: {self.webhook_type}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")
        await self.dispatch_embed()

    def determine_channel_id(self):
        channel_ids = {
            'nowplaying': PLEX_PLAYING,
            'nowresuming': PLEX_PLAYING,
            'finished': PLEX_PLAYING,
            'newcontent_episode': PLEX_CONTENT,
            'newcontent_season': PLEX_CONTENT,
            'newcontent_movie': PLEX_CONTENT,
        }
        return channel_ids.get(self.webhook_type, 'default_channel_id')

    def generate_embed(self):
        # Use a dictionary to map event types to their respective embed creation methods
        embed_creators = {
            'nowplaying': self.embed_for_nowplaying,
            'nowresuming': self.embed_for_nowresuming,
            'finished': self.embed_for_finished,
            'newcontent_episode': self.embed_for_newcontent_episode,
            'newcontent_season': self.embed_for_newcontent_season,
            'newcontent_movie': self.embed_for_newcontent_movie,
        }

        # Get the embed creation method for the event type
        generate_embed = embed_creators.get(self.webhook_type)

        # Call the embed creation method and return the embed
        return generate_embed()
    
    def embed_for_nowplaying(self):
        description = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = EmbedBuilder(title="Playing on Plex", description=f"{description}", color=0xe5a00d)
        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        embed.set_footer(text=f"{self.username} • {self.video_decision} • {self.product}", icon_url=PLEX_ICON)
        return embed
    
    def embed_for_nowresuming(self):
        description = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = EmbedBuilder(title="Resuming on Plex", description=f"{description}", color=0xe5a00d)
        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        embed.set_footer(text=f"{self.username} • {self.video_decision} • {self.product}", icon_url=PLEX_ICON)
        return embed
    
    def embed_for_finished(self):
        description = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = EmbedBuilder(title="Finished on Plex", description=f"{description}", color=0xe5a00d)
        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        embed.set_footer(text=f"{self.username} • {self.video_decision} • {self.product}", icon_url=PLEX_ICON)
        return embed
    
    def embed_for_newcontent_episode(self):
        description = f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = EmbedBuilder(title="New Episode added to Plex", description=description, color=0xe5a00d)
        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        embed.set_footer(text=f"{self.server_name}", icon_url=PLEX_ICON)
        return embed
    
    def embed_for_newcontent_season(self):
        description = f"{self.title}\n\nSeason {self.season_number} ({self.episode_count} episodes)"
        embed = EmbedBuilder(title="New Season added to Plex", description=description, color=0xe5a00d)
        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        embed.set_footer(text=f"{self.server_name}", icon_url=PLEX_ICON)
        return embed
    
    def embed_for_newcontent_movie(self):
        description = f"[{self.title} ({self.year})]({self.imdb_url})"
        embed = EmbedBuilder(title="New Movie added to Plex", description=description, color=0xe5a00d)
        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        embed.set_footer(text=f"{self.genres}", icon_url=PLEX_ICON)
        return embed
    
    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)  # Get the Channel object using the ID
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")