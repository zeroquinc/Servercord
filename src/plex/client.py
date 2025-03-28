import json
import requests
import os
from PIL import Image
from io import BytesIO
import numpy as np
from sklearn.cluster import KMeans

from config.globals import PLEX_ICON, PLEX_PLAYING, PLEX_CONTENT
from src.tmdb.client import TMDb
from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger

CACHE_FILE = 'cache.json'

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

    def format_remaining_time(self):
        if self.remaining_time and self.remaining_time != 'N/A':
            try:
                hours, minutes = map(int, self.remaining_time.split(":"))
                if hours == 0:
                    return f"{minutes}m"
                return f"{hours}h {minutes}m"
            except ValueError:
                logger.error(f"Invalid remaining_time format: {self.remaining_time}")
                return self.remaining_time
        return 'N/A'

    def get_image_from_url(self, url):
        """Fetch image data from the URL, save it locally, and return the path."""
        try:
            if not url.endswith(('jpg', 'jpeg', 'png', 'gif')):
                if 'imgur.com' in url:
                    img_id = url.split('/')[-1]
                    url = f'https://i.imgur.com/{img_id}.jpg'
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img_path = 'temp_image.jpg'
            with open(img_path, 'wb') as f:
                f.write(img_data.getbuffer())
            return img_path
        except Exception as e:
            logger.error(f"Error downloading image {url}: {e}")
            return None

    def cache_color(self, image_url, num_clusters=5):
        """Extracts the most representative and vibrant color from an image while avoiding excessive black/white."""
        cached_data = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cached_data = json.load(f)
                if image_url in cached_data:
                    logger.debug(f"Using cached color for {image_url}")
                    return cached_data[image_url]

        try:
            img_path = self.get_image_from_url(image_url)
            if not img_path:
                return 0xFFFFFF  # Default white color

            img = Image.open(img_path).convert("RGB")
            img = img.resize((200, 200))  # Resize for efficiency
            img_data = np.array(img).reshape((-1, 3))

            # Improved filtering logic (check if R, G, and B are not close to each other)
            mask = np.all((img_data > [50, 50, 50]) & (img_data < [230, 230, 230]), axis=1)  # Keep only non-near-black/white colors
            filtered_pixels = img_data[mask]

            if len(filtered_pixels) == 0:
                return 0xFFFFFF  # Return white if all colors are filtered out

            # Cluster colors using KMeans
            kmeans = KMeans(n_clusters=num_clusters, random_state=0, n_init=10)
            kmeans.fit(filtered_pixels)

            cluster_centers = kmeans.cluster_centers_
            labels, counts = np.unique(kmeans.labels_, return_counts=True)

            # Updated colorfulness function to consider red properly
            def colorfulness(c):
                r, g, b = c
                # Calculate the chromatic contrast (color difference) in RGB space
                rg = abs(r - g)
                yb = abs(0.5 * (r + g) - b)

                # Add a weighted factor for brightness contrast
                brightness = np.mean(c)
                brightness_factor = 1 - (abs(brightness - 128) / 128)

                # Return colorfulness based on chromatic contrast and brightness factor
                return (rg + yb) * brightness_factor

            # Rank clusters by frequency and colorfulness
            ranked_clusters = sorted(
                zip(cluster_centers, counts),
                key=lambda x: (colorfulness(x[0]), x[1]),  # Sort by colorfulness, then frequency
                reverse=True
            )

            distinct_color = ranked_clusters[0][0]  # Pick the best-ranked color

            # Convert RGB to hex
            distinct_color_hex = int(f'0x{int(distinct_color[0]):02x}{int(distinct_color[1]):02x}{int(distinct_color[2]):02x}', 16)

            # Cache the result
            cached_data[image_url] = distinct_color_hex
            with open(CACHE_FILE, 'w') as f:
                json.dump(cached_data, f)

            return distinct_color_hex

        except Exception as e:
            logger.error(f"Error processing image {image_url}: {e}")
            return 0xFFFFFF  # Default white color

    def get_embed_color(self):
        return self.cache_color(self.poster_url)

    async def handle_webhook(self):
        logger.debug(f"Received Plex payload: {json.dumps(self.payload, indent=4)}")
        if self.webhook_type == 'nowplaying' or self.webhook_type == 'nowresuming':
            logger.info(f"Sending Plex webhook for {self.title} from user {self.username}.")
        elif self.webhook_type.startswith('newcontent'):
            logger.info(f"Sending Plex webhook for new {self.media_type}: {self.title}.")
        await self.dispatch_embed()

    def determine_channel_id(self):
        channel_ids = {
            'nowplaying': PLEX_PLAYING,
            'nowresuming': PLEX_PLAYING,
            'newcontent_episode': PLEX_CONTENT,
            'newcontent_season': PLEX_CONTENT,
            'newcontent_movie': PLEX_CONTENT,
        }
        return channel_ids.get(self.webhook_type, 'default_channel_id')

    def generate_embed(self):
        embed_color = self.get_embed_color()  # Get color based on webhook type

        embed_creators = {
            'nowplaying': self.embed_for_playing,
            'nowresuming': self.embed_for_resuming,
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
        embed.set_author(name="Plex: Media Playing", icon_url=PLEX_ICON)
        embed.add_field(name="User", value=self.username, inline=True)
        embed.add_field(name="Method", value=self.video_decision.title(), inline=True)
        if self.product == "PM4K":
            self.product = "PlexMod for Kodi"
        embed.add_field(name="Client", value=self.product, inline=True)
        return embed

    def embed_for_resuming(self, color):
        description = f"Remaining time: {self.format_remaining_time()}"
        title = f"{self.title} ({self.year})" if self.media_type == "movie" else f"{self.title} (S{self.season_num00}E{self.episode_num00})"
        embed = EmbedBuilder(title=title, description=description, url=self.plex_url, color=color)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        embed.set_author(name="Plex: Media Resumed", icon_url=PLEX_ICON)
        embed.add_field(name="User", value=self.username, inline=True)
        embed.add_field(name="Method", value=self.video_decision.title(), inline=True)
        if self.product == "PM4K":
            self.product = "PlexMod for Kodi"
        embed.add_field(name="Client", value=self.product, inline=True)
        return embed

    def embed_for_newcontent(self, color):
        embed = EmbedBuilder(title=self.get_newcontent_title(), url=self.plex_url, color=color)
        if self.summary:
            embed.add_field(name="Summary", value=self.summary, inline=False)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        if self.webhook_type == 'newcontent_episode':
            if self.format_duration_time():
                embed.add_field(name="Runtime", value=self.format_duration_time(), inline=False)
            embed.set_footer(text=f"Aired on {self.air_date}")
        elif self.webhook_type == 'newcontent_season':
            embed.add_field(name="Episodes", value=f"{self.episode_count}", inline=False)
        elif self.webhook_type == 'newcontent_movie':
            backdrop_url = TMDb.movie_backdrop_path(self.tmdb_id_plex)
            if self.format_duration_time():
                embed.add_field(name="Runtime", value=self.format_duration_time(), inline=False)
            if backdrop_url:
                embed.set_image(url=backdrop_url)
            if self.genres and self.genres.lower() != "n/a":
                embed.add_field(name="Genres", value=self.genres, inline=False)
        links = self.build_links()
        if links:
            embed.add_field(name="Links", value=links, inline=False)
        # footer_text = self.build_footer()
        # embed.set_footer(text=footer_text)
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

    # def build_footer(self):
    #     footer_parts = []
    #     if self.genres and self.genres.lower() != "n/a":
    #         footer_parts.append(self.genres)
    #     footer_parts.append(self.format_duration_time())
    #     return " • ".join(footer_parts)

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")