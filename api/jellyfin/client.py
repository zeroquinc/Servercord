from datetime import datetime
import time
from config.globals import JELLYFIN_ICON, JELLYFIN_PLAYING, JELLYFIN_CONTENT
from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger
from api.tmdb.client import TMDb

class JellyfinWebhookHandler:
    item_cache = {}  # Stores temporary ItemAdded events

    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.details = None

    def extract_details(self):  
        try:
            logger.debug("Extracting details from Jellyfin payload.")

            data = {k: self.payload.get(k, {}) for k in ["Event", "Item", "User", "Session", "Server", "Series"]}
            media = data["Item"]
            series = data["Series"]
            media_type = media.get("Type", "Unknown")
            item_id = media.get("Id")
            event_type = data["Event"]

            if not item_id:
                logger.warning("Item ID missing, skipping event.")
                return None

            # Handle ItemAdded logic
            if event_type == "ItemAdded":
                logger.info(f"Storing ItemAdded event for ID {item_id}.")
                self.item_cache[item_id] = {
                    "timestamp": time.time(),
                    "data": data
                }
                return None  # Do not process yet

            # Handle ItemUpdated logic
            if event_type == "ItemUpdated":
                if "MetadataDownload" not in self.payload.get("AdditionalData", []):
                    logger.info("Ignoring ItemUpdated event without MetadataDownload.")
                    return None

                # Check if a corresponding ItemAdded exists
                if item_id in self.item_cache:
                    logger.info(f"Matching ItemUpdated found for ItemAdded ID {item_id}. Processing event.")
                    cached_data = self.item_cache.pop(item_id)  # Remove from cache
                    data = cached_data["data"]  # Use stored ItemAdded data

                else:
                    logger.info(f"ItemUpdated received without prior ItemAdded for ID {item_id}, processing normally.")

            # Process media details
            media_details = self.extract_media_details(media, series, media_type)
            user_details = self.extract_user_details(data["User"])
            session_details = self.extract_session_details(data["Session"])
            server_details = self.extract_server_details(data["Server"])

            result = {
                "event": event_type,
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

    @classmethod
    def cleanup_cache(cls, max_age=300):
        """Remove old entries from the item cache (default: 5 minutes)."""
        current_time = time.time()
        expired_keys = [key for key, value in cls.item_cache.items() if current_time - value["timestamp"] > max_age]

        for key in expired_keys:
            del cls.item_cache[key]
            logger.info(f"Removed expired ItemAdded event from cache: {key}")

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
        play_method = session.get("PlayState", {}).get("PlayMethod", "Unknown")

        if play_method == "DirectStream":
            play_method = "Direct Play"

        return {
            "device_name": session.get("DeviceName", "Unknown Device"),
            "client": session.get("Client", "Unknown Client"),
            "remote_ip": session.get("RemoteEndPoint", "Unknown IP"),
            "is_paused": session.get("PlayState", {}).get("IsPaused", False),
            "play_method": play_method,
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

    def determine_channel_id(self):
        return {
            'Play': JELLYFIN_PLAYING,
            'Resume': JELLYFIN_PLAYING,
            'Pause': JELLYFIN_PLAYING,
            'ItemUpdated': JELLYFIN_CONTENT
        }.get(self.details.get('event'), 'default_channel_id')

    def get_embed_color(self):
        return {
            'Play': 0x6c76cc,
            'Resume': 0xc034eb,
            'Pause': 0x6e0918,
            'ItemUpdated': 0x1e90ff,
        }.get(self.details.get('event'), 0x000000)

    def generate_embed(self):  
        embed_color = self.get_embed_color()
        return {
            'Play': self.embed_for_playing,
            'Resume': self.embed_for_resuming,
            'Pause': self.embed_for_pausing,
            'ItemUpdated': self.embed_for_newcontent
        }.get(self.details.get('event'), lambda _: None)(embed_color)

    def embed_for_playing(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])

        embed.set_author(name="Playing on Jellyfin", icon_url=JELLYFIN_ICON)
        embed.set_footer(text=f"{self.details['user']['username']} • {self.details['session']['play_method']} • {self.details['session']['client']}")

        return embed
    
    def embed_for_resuming(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])

        embed.set_author(name="Resuming on Jellyfin", icon_url=JELLYFIN_ICON)
        embed.set_footer(text=f"{self.details['user']['username']} • {self.details['session']['play_method']} • {self.details['session']['client']}")

        return embed
    
    def embed_for_pausing(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])

        embed.set_author(name="Paused on Jellyfin", icon_url=JELLYFIN_ICON)
        embed.set_footer(text=f"{self.details['user']['username']} • {self.details['session']['play_method']} • {self.details['session']['client']}")

        return embed

    def embed_for_newcontent(self, color):
        media = self.details['media']
        title = self.format_media_title(media)
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

        # Build and add links field
        links = self.build_links()
        if links:
            embed.add_field(name="Links", value=links, inline=False)

        if media.get("poster_url"):
            embed.set_thumbnail(url=media["poster_url"])
            
        embed.set_author(name=f"New {media['type']} added to Jellyfin", icon_url=JELLYFIN_ICON)
        return embed

    def build_links(self):
        media = self.details['media']
        links = [f"[{url['Name']}]({url['Url']})" for url in media.get("external_urls", []) if url['Name'] in ['IMDb', 'TMDb', 'Trakt']]

        # Only add YouTube trailer for Movies
        if media.get("type") == "Movie":
            youtube_url = self.get_youtube_trailer()
            if youtube_url:
                links.append(f"[YouTube]({youtube_url})")

        return " • ".join(links)

    def get_youtube_trailer(self):
        media = self.details['media']
        trailers = media.get("remote_trailers", [])

        if not trailers:
            return None

        # Look for an "Official Trailer"
        for trailer in trailers:
            if trailer.get("Name") == "Official Trailer":
                return trailer["Url"]

        # Look for any trailer containing "Trailer" in its name
        for trailer in trailers:
            if "Trailer" in trailer.get("Name", ""):
                return trailer["Url"]

        # Fallback to the first available trailer
        return trailers[0]["Url"]
        
    def build_footer(self, media):
        footer_parts = []
        
        if media.get("type") == "Movie":
            genres = ", ".join(media.get("genres", [])) or "N/A"
            if genres.lower() != "n/a":
                footer_parts.append(genres)
            
            # Add runtime if available
            if media.get("runtime_seconds"):
                duration = f"{int(media['runtime_seconds'] // 60)} min"
                footer_parts.append(duration)

        # Add PremiereDate for Episodes
        if media["type"] == "Episode" and media.get("premiere_date"):
            premiere_date = self.format_premiere_date(media["premiere_date"])
            footer_parts.append(f"Aired on {premiere_date}")

        return " • ".join(footer_parts)
    
    def format_premiere_date(self, date_str):
        """Formats a premiere date into DD/MM/YYYY format."""
        if not date_str:
            return "Unknown Date"
        
        try:
            # Remove trailing 'Z' and parse
            date_obj = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return "Unknown Date"
        
    async def handle_webhook(self):
        media_type = self.payload.get("Item", {}).get("Type", "Unknown")
        
        if media_type in ["Person", "Folder"]:
            logger.info(f"Blocking webhook request for media type: {media_type}")
            return  # Stop processing immediately

        self.details = self.extract_details()
        
        if self.details is None:
            logger.info("Skipping webhook processing as details are None.")
            return

        logger.info(f"Processing Jellyfin webhook payload for event type: {self.details.get('event', 'Unknown Event')}")
        await self.dispatch_embed()

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")