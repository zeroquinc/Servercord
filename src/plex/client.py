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
            'imdb_url', 'imdb_id', 'tvdb_url', 'trakt_url', 'plex_url', 'tmdb_url', 'tmdb_id_plex', 'critic_rating', 'audience_rating',
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

    def format_duration_time(self):
        if self.duration_time and self.duration_time != 'N/A':
            try:
                hours, minutes = map(int, self.duration_time.split(":"))  # Convert to integers to handle non-padded hours/minutes
                if hours == 0:
                    return f"{minutes}m"  # Only show minutes if hours are 0
                return f"{hours}h {minutes}m"
            except ValueError:
                logger.error(f"Invalid duration_time format: {self.duration_time}")
                return self.duration_time
        return 'N/A'

    async def handle_webhook(self):
        logger.debug(f"Received Plex payload: {json.dumps(self.payload, indent=4)}")
        if self.webhook_type == 'nowplaying':
            logger.info(f"Sending Plex webhook for {self.title} from user {self.username}.")
        elif self.webhook_type.startswith('newcontent'):
            logger.info(f"Sending Plex webhook for new {self.media_type}: {self.title}.")
        await self.dispatch_embed()

    def determine_channel_id(self):
        channel_ids = {
            'nowplaying': PLEX_PLAYING,
            'newcontent_episode': PLEX_CONTENT,
            'newcontent_season': PLEX_CONTENT,
            'newcontent_movie': PLEX_CONTENT,
        }
        return channel_ids.get(self.webhook_type, 'default_channel_id')

    def get_embed_color(self):
        color_mapping = {
            'nowplaying': 0xe5a00d,           # Orange color for now playing
            'newcontent_episode': 0x1e90ff,   # Blue color for new episode content
            'newcontent_season': 0x32cd32,    # Lime green color for new season content
            'newcontent_movie': 0xff6347      # Tomato red color for new movie content
        }
        return color_mapping.get(self.webhook_type, 0x000000)  # Default to black if not found

    def generate_embed(self):
        embed_color = self.get_embed_color()  # Get color based on webhook type

        embed_creators = {
            'nowplaying': self.embed_for_playing,
            'newcontent_episode': self.embed_for_newcontent,
            'newcontent_season': self.embed_for_newcontent,
            'newcontent_movie': self.embed_for_newcontent,
        }
        return embed_creators.get(self.webhook_type)(embed_color)

    def embed_for_playing(self, color):
        title = f"{self.title} ({self.year})" if self.media_type == "movie" else f"{self.title} (S{self.season_num00}E{self.episode_num00})"
        embed = EmbedBuilder(title=title, url=self.plex_url, color=color)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        embed.set_author(name="Plex: Playing Media", icon_url=PLEX_ICON)
        embed.add_field(name="User", value=self.username.capitalize(), inline=True)
        embed.add_field(name="Method", value=self.video_decision.title(), inline=True)
        embed.add_field(name="Client", value=self.player.capitalize(), inline=True)
        return embed

    def embed_for_newcontent(self, color):
        embed = EmbedBuilder(title=self.get_newcontent_title(), url=self.plex_url, color=color)
        if self.summary:
            if self.webhook_type in ['newcontent_episode', 'newcontent_season']:
                embed.add_field(name="Plot", value=f"||{self.summary}||", inline=False)
            else:
                embed.add_field(name="Plot", value=self.summary, inline=False)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        if self.webhook_type == 'newcontent_episode':
            embed.set_footer(text=f"Aired on {self.air_date}")
        elif self.webhook_type == 'newcontent_season':
            embed.add_field(name="Episodes", value=f"{self.episode_count}", inline=False)
        if self.webhook_type == 'newcontent_movie':
            footer_text = self.build_footer()
            embed.set_footer(text=footer_text)
        links = self.build_links()
        if links:
            embed.add_field(name="Links", value=links, inline=False)
        embed.set_author(name=f"Plex: New {self.media_type.capitalize()} added", icon_url=PLEX_ICON)
        return embed

    def get_newcontent_title(self):
        titles = {
            'newcontent_episode': f"{self.title} (S{self.season_num00}E{self.episode_num00})",
            'newcontent_season': f"{self.title}",
            'newcontent_movie': f"{self.title} ({self.year})"
        }
        return titles.get(self.webhook_type, self.title)
    
    def build_links(self):
        links = [
            f"[IMDb]({self.imdb_url})" for url in [self.imdb_url] if url and url.lower() != "n/a"
        ] + [
            f"[TMDb]({self.tmdb_url})" for url in [self.tmdb_url] if url and url.lower() != "n/a"
        ]

        if self.imdb_id and self.imdb_id.lower() != "n/a":
            trakt_urls = {
                'newcontent_movie': f"https://trakt.tv/movie/{self.imdb_id}",
                'newcontent_episode': f"https://trakt.tv/episode/{self.imdb_id}",
                'newcontent_season': f"https://trakt.tv/shows/{self.imdb_id}"
            }
            links.append(f"[Trakt]({trakt_urls.get(self.webhook_type)})")

        return " • ".join(links)

    def build_footer(self):
        footer_parts = []
        if self.genres and self.genres.lower() != "n/a":
            footer_parts.append(self.genres)
        footer_parts.append(self.format_duration_time())
        return " • ".join(footer_parts)

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")