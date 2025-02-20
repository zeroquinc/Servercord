import json
from datetime import datetime
from config.globals import JELLYFIN_ICON, JELLYFIN_PLAYING, JELLYFIN_CONTENT
from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger
from api.tmdb.client import TMDb

class JellyfinWebhookHandler:
    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.details = self.extract_details()

    def extract_details(self):  
        try:
            logger.debug("Extracting details from Jellyfin payload.")

            data = {k: self.payload.get(k, {}) for k in ["Event", "Item", "User", "Session", "Server", "Series"]}
            media = data["Item"]
            series = data["Series"]
            media_type = media.get("Type", "Unknown")

            if media_type == "Person":
                logger.info("Ignoring event for Person type.")
                return None  

            if data["Event"] == "ItemUpdated" and "MetadataImport" not in self.payload.get("AdditionalData", []):
                logger.info("Ignoring ItemUpdated event without MetadataImport.")
                return None

            media_details = self.extract_media_details(media, series, media_type)
            user_details = self.extract_user_details(data["User"])
            session_details = self.extract_session_details(data["Session"])
            server_details = self.extract_server_details(data["Server"])

            result = {
                "event": data["Event"],
                "timestamp": datetime.utcnow().isoformat(),
                "media": media_details,
                "user": user_details,
                "session": session_details,
                "server": server_details,
            }

            logger.debug(f"Returning details: {result}")
            return result

        except Exception as e:
            logger.error(f"Error extracting details: {e}")
            return None

    def extract_media_details(self, media, series, media_type):
        details = {
            "type": media_type,
            "name": media.get("Name", "Unknown"),
            "overview": media.get("Overview", "No overview available."),
            "file_path": media.get("Path", "Unknown path"),
            "official_rating": media.get("OfficialRating", "Not Rated"),
            "genres": media.get("Genres", []),
            "community_rating": media.get("CommunityRating", "N/A"),
            "production_year": media.get("ProductionYear", "N/A"),
            "premiere_date": media.get("PremiereDate", "N/A"),
            "is_hd": media.get("IsHD", False),
            "runtime_seconds": media.get("RunTimeTicks", 0) / 10_000_000 if media.get("RunTimeTicks") else 0,
            "provider_ids": media.get("ProviderIds", {}),
            "external_urls": media.get("ExternalUrls", []),
            "poster_url": self.get_poster_url(media, series, media_type),
        }

        if media_type == "Movie":
            details.update({
                "critic_rating": media.get("CriticRating", "N/A"),
                "production_locations": media.get("ProductionLocations", []),
                "taglines": media.get("Taglines", []),
                "remote_trailers": media.get("RemoteTrailers", []),
            })
        elif media_type == "Episode":
            details.update({
                "season": media.get("ParentIndexNumber", "N/A"),
                "episode": media.get("IndexNumber", "N/A"),
                "series": self.extract_series_details(series)
            })
        return details

    def extract_series_details(self, series):
        return {
            "name": series.get("Name", "Unknown Series"),
            "overview": series.get("Overview", "No series overview available."),
            "community_rating": series.get("CommunityRating", "N/A"),
            "provider_ids": series.get("ProviderIds", {}),
            "premiere_date": series.get("PremiereDate", "Unknown"),
            "external_urls": series.get("ExternalUrls", []),
        }
        
    def extract_user_details(self, user):
        return {
            "username": user.get("Name", "Unknown User"),
            "user_id": user.get("Id", "Unknown ID"),
            "is_admin": user.get("Policy", {}).get("IsAdministrator", False),
            "last_login": user.get("LastLoginDate", "Unknown"),
        }

    def extract_session_details(self, session):
        return {
            "device_name": session.get("DeviceName", "Unknown Device"),
            "client": session.get("Client", "Unknown Client"),
            "remote_ip": session.get("RemoteEndPoint", "Unknown IP"),
            "is_paused": session.get("PlayState", {}).get("IsPaused", False),
            "play_method": session.get("PlayState", {}).get("PlayMethod", "Unknown"),
        }

    def extract_server_details(self, server):
        return {
            "server_name": server.get("Name", "Unknown Server"),
            "server_version": server.get("Version", "Unknown Version"),
        }

    def get_poster_url(self, media, series, media_type):
        if media_type == "Episode":
            tvdb_id = series.get("ProviderIds", {}).get("Tvdb")
            return TMDb.show_poster_path(tvdb_id) if tvdb_id else None
        else:
            tmdb_id = media.get("ProviderIds", {}).get("Tmdb")
            return TMDb.movie_poster_path(tmdb_id) if tmdb_id else None

    def format_media_title(self, media):
        if media['type'] == "Movie":
            return f"{media['name']} ({media['production_year']})"
        elif media['type'] == "Episode":
            season = f"S{int(media.get('season', 0)):02}"
            episode = f"E{int(media.get('episode', 0)):02}"
            return f"{media['series']['name']} - {media['name']} ({season}{episode})"
        else:
            return f"{media['name']} (Unknown Type)"

    async def handle_webhook(self):
        if self.details is None:
            logger.info("Skipping webhook processing as details are None.")
            return

        logger.info(f"Processing Jellyfin webhook payload for event type: {self.details.get('event', 'Unknown Event')}")
        await self.dispatch_embed()

    def determine_channel_id(self):
        return {
            'Play': JELLYFIN_PLAYING,
            'Resume': JELLYFIN_PLAYING,
            'ItemUpdated': JELLYFIN_CONTENT
        }.get(self.details.get('event'), 'default_channel_id')

    def get_embed_color(self):
        return {
            'Play': 0x6c76cc,
            'Resume': 0xc034eb,
            'ItemAdded': 0x1e90ff,
        }.get(self.details.get('event'), 0x000000)

    def generate_embed(self):  
        embed_color = self.get_embed_color()
        return {
            'Play': self.embed_for_playing,
            'Resume': self.embed_for_resuming,
            'ItemUpdated': self.embed_for_newcontent
        }.get(self.details.get('event'), lambda _: None)(embed_color)

    def embed_for_playing(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])

        embed.set_author(name="Now Playing on Jellyfin", icon_url=JELLYFIN_ICON)
        embed.set_footer(text=f"{self.details['user']['username']} • {self.details['session']['play_method']} • {self.details['session']['client']}")

        return embed
    
    def embed_for_resuming(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])

        embed.set_author(name="Now Resuming on Jellyfin", icon_url=JELLYFIN_ICON)
        embed.set_footer(text=f"{self.details['user']['username']} • {self.details['session']['play_method']} • {self.details['session']['client']}")

        return embed

    def embed_for_newcontent(self, color):
        media = self.details['media']
        title = self.get_newcontent_title(media)
        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        # Format plot with spoilers if it's an Episode or Series
        plot = media.get("overview", "No overview available.")
        if media["type"] in ["Episode", "Series"]:
            plot = f"||{plot}||"  # Wrap in Discord spoiler tags

        embed.add_field(name="Plot", value=plot, inline=False)

        # Build and add footer (Genres for Movies, PremiereDate for Episodes)
        footer_text = self.build_footer(media)
        if footer_text:
            embed.set_footer(text=footer_text)

        links = self.build_links()
        if links:
            embed.add_field(name="Links", value=links, inline=False)

        if media.get("poster_url"):
            embed.set_thumbnail(url=media["poster_url"])
        return embed

    def get_newcontent_title(self, media):
        titles = {
            'Episode': f"{media['name']} (S{int(media.get('season', 0)):02}E{int(media.get('episode', 0)):02})",
            'Season': f"{media['name']}",
            'Movie': f"{media['name']} ({media['production_year']})"
        }
        return titles.get(media['type'], media['name'])

    def build_links(self):
        media = self.details['media']
        links = []
        for url in media.get("external_urls", []):
            if url['Name'] in ['IMDb', 'TMDb', 'Trakt']:
                links.append(f"[{url['Name']}]({url['Url']})")
        return " • ".join(links)
    
    def build_footer(self, media):
        footer_parts = []
        
        if media["type"] == "Movie":
            genres = ", ".join(media.get("genres", [])) if media.get("genres") else "N/A"
            if genres.lower() != "n/a":
                footer_parts.append(genres)

        # Add PremiereDate for Episodes
        if media["type"] == "Episode" and media.get("premiere_date"):
            premiere_date = self.format_premiere_date(media["premiere_date"])
            footer_parts.append(f"Air date: {premiere_date}")

        # Add runtime if available
        if media.get("runtime_seconds"):
            duration = f"{int(media['runtime_seconds'] // 60)} min"
            footer_parts.append(duration)

        return " • ".join(footer_parts)
    
    def format_premiere_date(self, date_str):
        """Formats a premiere date into DD/MM/YYYY format."""
        try:
            return datetime.fromisoformat(date_str.rstrip("Z")).strftime("%d/%m/%Y")
        except ValueError:
            return "Unknown Date"

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")