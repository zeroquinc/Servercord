from config.globals import JELLYFIN_ICON, JELLYFIN_PLAYING, JELLYFIN_CONTENT
from src.discord.embed import EmbedBuilder
from src.tmdb.client import TMDb
from utils.custom_logger import logger
import json

class JellyfinWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.extract_details()

    def extract_details(self):
        field_mappings = {
            'server_id': 'ServerId',
            'server_name': 'ServerName',
            'server_version': 'ServerVersion',
            'server_url': 'ServerUrl',
            'webhook_type': 'NotificationType',
            'timestamp': 'Timestamp',
            'utc_timestamp': 'UtcTimestamp',
            'title': 'Name',
            'summary': 'Overview',
            'item_id': 'ItemId',
            'media_type': 'ItemType',
            'duration_time': 'RunTime',
            'year': 'Year',
            'release_date': 'PremiereDate',
            'series_name': 'SeriesName',
            'series_id': 'SeriesId',
            'season_id': 'SeasonId',
            'series_premiere_date': 'SeriesPremiereDate',
            'season_num': 'SeasonNumber',
            'season_num00': 'SeasonNumber00',
            'episode_num': 'EpisodeNumber',
            'episode_num00': 'EpisodeNumber00',
            'genres': 'Genres',
            'imdb_id': 'Provider_imdb',
            'tvdb_id': 'Provider_tvdb',
            'tmdb_id': 'Provider_tmdb',
            'imdb_id_show': 'Provider_imdb_Show',
            'tvdb_id_show': 'Provider_tvdb_Show',
            'tmdb_id_show': 'Provider_tmdb_Show',
            'username': 'NotificationUsername',
            'device_name': 'DeviceName',
            'client_name': 'ClientName',
            'video_decision': 'PlayMethod',
            'last_activity': 'LastActivityDate',
            'last_playback_check': 'LastPlaybackCheckIn',
            'remote_ip': 'RemoteEndPoint'
        }

        for attr, key in field_mappings.items():
            value = self.payload.get(key, 'N/A')
            setattr(self, attr, value)
            logger.debug(f"Set {attr} to {value}")

        # Fetch poster URL
        self.poster_url = self.fetch_poster_url()
        
        logger.debug(f"Poster URL: {self.poster_url}")

        # Generate IMDb, TVDb, and TMDb URLs
        self.imdb_url, self.tmdb_url = self.generate_external_urls()
        
        logger.debug(f"External URLs: IMDb: {self.imdb_url}, TMDb: {self.tmdb_url}")

    def fetch_poster_url(self):
        """Fetch the appropriate poster URL based on media type."""
        if self.media_type.lower() == "movie" and self.tmdb_id != 'N/A':
            return TMDb.movie_poster_path(self.tmdb_id)
        elif self.media_type.lower() == "episode" and self.tvdb_id != 'N/A':
            return TMDb.show_poster_path(self.tvdb_id_show)
        return None  # No poster found

    def generate_external_urls(self):
        """Generate external URLs based on available IDs and media type."""
        imdb_url = 'N/A'
        tmdb_url = 'N/A'

        if self.media_type.lower() == "movie":
            imdb_url = f"https://www.imdb.com/title/{self.imdb_id}" if self.imdb_id != 'N/A' else 'N/A'
            tmdb_url = f"https://www.themoviedb.org/movie/{self.tmdb_id}" if self.tmdb_id != 'N/A' else 'N/A'
        
        elif self.media_type.lower() in ["episode", "series"]:
            imdb_url = f"https://www.imdb.com/title/{self.imdb_id_show}" if self.imdb_id_show != 'N/A' else 'N/A'
            tmdb_url = f"https://www.themoviedb.org/tv/{self.tmdb_id}" if self.tmdb_id != 'N/A' else 'N/A'

        return imdb_url, tmdb_url

    async def handle_webhook(self):
        logger.debug(f"Received Jellyfin payload: {json.dumps(self.payload, indent=4)}")
        if self.webhook_type == 'PlaybackStart':
            logger.info(f"Sending Jellyfin webhook for {self.title} from user {self.username}.")
        elif self.webhook_type.startswith('ItemAdded'):
            logger.info(f"Sending Jellyfin webhook for new {self.media_type}: {self.title}.")
        await self.dispatch_embed()

    def determine_channel_id(self):
        channel_ids = {
            'PlaybackStart': JELLYFIN_PLAYING,
            'ItemAdded': JELLYFIN_CONTENT,
        }
        return channel_ids.get(self.webhook_type, 'default_channel_id')

    def get_embed_color(self):
        color_mapping = {
            'PlaybackStart': 0x6c76cc,
            'ItemAdded': 0x1e90ff,
        }
        return color_mapping.get(self.webhook_type, 0x000000)  # Default to black if not found

    def generate_embed(self):
        embed_color = self.get_embed_color()  # Get color based on webhook type

        embed_creators = {
            'PlaybackStart': self.embed_for_playing,
            'ItemAdded': self.embed_for_newcontent,
        }
        return embed_creators.get(self.webhook_type)(embed_color)

    def embed_for_playing(self, color):
        # Determine the primary URL based on media type
        if self.media_type == "Movie":
            media_url = self.imdb_url if self.imdb_url != "N/A" else self.tmdb_url
        elif self.media_type == "Episode":
            media_url = self.imdb_url if self.imdb_url != "N/A" else self.tvdb_url
        else:
            media_url = "N/A"

        # Format title
        title = f"{self.title} ({self.year})" if self.media_type == "Movie" else f"{self.series_name} - {self.title} (S{self.season_num00}E{self.episode_num00})"

        # Create embed
        embed = EmbedBuilder(title=title, url=media_url, color=color)
        
        # Add poster if available
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)

        # Set author and other fields
        embed.set_author(name="Jellyfin: Media Playing", icon_url=JELLYFIN_ICON)
        embed.add_field(name="User", value=self.username, inline=True)
        embed.add_field(name="Method", value=self.video_decision, inline=True)
        embed.add_field(name="Client", value=self.client_name, inline=True)

        return embed

    def embed_for_newcontent(self, color):
        # Determine the primary URL based on media type
        if self.media_type == "Movie":
            media_url = self.imdb_url if self.imdb_url != "N/A" else self.tmdb_url
        elif self.media_type == "Episode":
            media_url = self.imdb_url if self.imdb_url != "N/A" else self.tvdb_url
        else:
            media_url = "N/A"

        embed = EmbedBuilder(title=self.get_newcontent_title(), url=media_url, color=color)
        if self.summary:
            if self.media_type == "Episode":
                embed.add_field(name="Plot", value=f"||{self.summary}||", inline=False)
            else:
                embed.add_field(name="Plot", value=self.summary, inline=False)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        if self.media_type == "Episode":
            embed.set_footer(text=f"Aired on {self.release_date}")
        if self.media_type == "Movie":
            footer_text = self.build_footer()
            embed.set_footer(text=footer_text)
        links = self.build_links()
        if links:
            embed.add_field(name="Links", value=links, inline=False)
        embed.set_author(name=f"Jellyfin: New {self.media_type.capitalize()} added", icon_url=JELLYFIN_ICON)
        return embed
    
    def get_newcontent_title(self):
        titles = {
            'Movie': f"{self.title} ({self.year})",
            'Episode': f"{self.series_name} - {self.title} (S{self.season_num00}E{self.episode_num00})"
        }
        return titles.get(self.media_type, self.title)

    def build_links(self):
        links = [
            f"[IMDb]({self.imdb_url})" for url in [self.imdb_url] if url and url.lower() != "n/a"
        ] + [
            f"[TMDb]({self.tmdb_url})" for url in [self.tmdb_url] if url and url.lower() != "n/a"
        ]

        if self.imdb_id and self.imdb_id.lower() != "n/a":
            trakt_urls = {
                'Movie': f"https://trakt.tv/movie/{self.imdb_id}",
                'Episode': f"https://trakt.tv/episode/{self.imdb_id}"
            }
            links.append(f"[Trakt]({trakt_urls.get(self.media_type)})")

        return " • ".join(links)
    
    def format_duration_time(self):
        if self.duration_time and self.duration_time != 'N/A':
            try:
                parts = list(map(int, self.duration_time.split(":")))
                if len(parts) == 3:  # HH:MM:SS format
                    hours, minutes, _ = parts
                elif len(parts) == 2:  # MM:SS format
                    hours, minutes = 0, parts[0]
                else:
                    raise ValueError("Invalid format")
                
                if hours == 0:
                    return f"{minutes}m"
                return f"{hours}h {minutes}m"
            except ValueError:
                logger.error(f"Invalid duration_time format: {self.duration_time}")
                return self.duration_time
        return 'N/A'
        

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