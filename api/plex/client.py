import json
import discord
from discord.utils import utcnow

from config.globals import PLEX_ICON, DISCORD_THUMBNAIL, PLEX_PLAYING, PLEX_CONTENT

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
        self.rating = self.payload.get('source_metadata_details', {}).get('rating', 'N/A')
        self.username = self.payload.get('stream_details', {}).get('username', 'N/A')
        self.product = self.payload.get('stream_details', {}).get('product', 'N/A')
        self.video_decision = self.payload.get('stream_details', {}).get('video_decision', 'N/A').capitalize()
        self.remaining_time = self.payload.get('stream_details', {}).get('remaining_time', 'N/A')
        self.duration_time = self.payload.get('stream_details', {}).get('duration_time', 'N/A')
        self.server_name = self.payload.get('server_info', {}).get('server_name', 'N/A')
        self.webhook_type = self.payload.get('server_info', {}).get('webhook_type', 'N/A')
        
    async def handle_webhook(self):
        logger.info(f"Processing Plex webhook payload for event type: {self.webhook_type}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")
        channel_id = self.determine_channel_id()
        await self.dispatch_embed(channel_id)

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
        generate_embed = embed_creators.get(self.webhook_type, self.embed_for_default)

        # Call the embed creation method and return the embed
        return generate_embed()
    
    def init_embed(self, title, color, author):
        embed = discord.Embed(title=title, color=color)
        embed.set_author(name=author, icon_url=PLEX_ICON)
        embed.url = self.imdb_url if self.imdb_url != 'N/A' else self.tvdb_url
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_image(url=DISCORD_THUMBNAIL)

        return embed
    
    def embed_for_nowplaying(self):
        embed_title = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = self.init_embed(embed_title, 0x1C4673, f"Plex - Streaming {self.media_type}")

        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        
        embed.add_field(name=":arrow_forward: Now Streaming", value=f"{self.remaining_time} remaining", inline=True)
        embed.set_footer(text=f"{self.server_name} | {self.username} | {self.product} | {self.video_decision}")

        return embed
    
    def embed_for_nowresuming(self):
        embed_title = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = self.init_embed(embed_title, 0x3587DE, f"Plex - Streaming {self.media_type}")

        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        
        embed.add_field(name=":play_pause: Now Resuming", value=f"{self.remaining_time} remaining", inline=True)
        embed.set_footer(text=f"{self.server_name} | {self.username} | {self.product} | {self.video_decision}")

        return embed
    
    def embed_for_finished(self):
        embed_title = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = self.init_embed(embed_title, 0x891836, f"Plex - Streaming {self.media_type}")

        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)
        
        embed.add_field(name=":white_check_mark: Finished", value=f"{self.duration_time} total", inline=True)
        embed.set_footer(text=f"{self.server_name} | {self.username} | {self.product} | {self.video_decision}")

        return embed
    
    def embed_for_newcontent_episode(self):
        embed_title = f"{self.title} (S{self.season_number}E{self.episode_number})"
        embed = self.init_embed(embed_title, 0xE91655, "Plex - New Episode")
        embed.description = self.summary

        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)

        fields = {
            "Quality": (self.quality, True),
            "Runtime": (self.remaining_time, True),
            "Air date": (self.air_date, True),
            }

        for name, (value, inline) in fields.items():
            embed.add_field(name=name, value=value, inline=inline)

        embed.set_footer(text=self.server_name)

        return embed
    
    def embed_for_newcontent_season(self):
        embed_title = self.title
        embed = self.init_embed(embed_title, 0x169CE9, "Plex - New Season")
        embed.description = self.summary

        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)

        fields = {
            "Season": (self.season_number, True),
            "Episodes": (self.episode_count, True),
            "Details": (f"[IMDb]({self.imdb_url})", True),
            }

        for name, (value, inline) in fields.items():
            embed.add_field(name=name, value=value, inline=inline)

        embed.set_footer(text=self.server_name)

        return embed
    
    def embed_for_newcontent_movie(self):
        embed_title = f"{self.title} ({self.year})"
        embed = self.init_embed(embed_title, 0x7CE916, "Plex - New Movie")
        embed.description = self.summary

        poster_path = self.poster_url
        if poster_path:
            embed.set_thumbnail(url=poster_path)

        fields = {
            "Quality": (self.quality, True),
            "Genres": (self.genres, True),
            "Release date": (self.release_date, True),
            "Rotten Tomatoes": (f":popcorn: {self.rating}", True),
            "Runtime": (self.remaining_time, True),
        }

        for name, (value, inline) in fields.items():
            embed.add_field(name=name, value=value, inline=inline)

        embed.set_footer(text=self.server_name)

        return embed

    def embed_for_default(self):
        embed = discord.Embed (title=" ")
        return embed
    
    async def dispatch_embed(self, channel_id):
        embed = self.generate_embed()
        await self.discord_bot.dispatch_embed(channel_id, embed)