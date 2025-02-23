from datetime import datetime, timezone
from config.globals import JELLYFIN_ICON, JELLYFIN_PLAYING, JELLYFIN_CONTENT
from src.discord.embed import EmbedBuilder
from src.tmdb.client import TMDb
from utils.custom_logger import logger
from src.jellyfin.cache import EventCache

class JellyfinWebhookHandler:
    cache = EventCache()

    def __init__(self, payload, discord_bot):
        self.payload = payload
        self.discord_bot = discord_bot
        self.details = None
        
    async def handle_webhook(self):
        """ Main function to handle the webhook event. """
        event_type = self.payload.get("Event")
        media_type = self.payload.get("Item", {}).get("Type", "Unknown")

        if self.is_blocked_media_type(media_type):
            return

        if event_type == "Play":
            await self.handle_play_event()
            return

        file_id = self.get_file_id()
        if not file_id:
            logger.warning("No File Id found, skipping event.")
            return

        if not self.is_valid_item(file_id):
            return

        if event_type == "ItemAdded":
            await self.handle_item_added(file_id)
            return

        if event_type == "ItemUpdated":
            await self.handle_item_updated(file_id)

    def extract_details(self):
        try:
            logger.debug("Extracting details from Jellyfin payload.")
            data = {k: self.payload.get(k, {}) for k in ["Event", "Item", "User", "Session", "Server", "Series"]}
            media = data["Item"]
            series = data["Series"]
            media_type = media.get("Type", "Unknown")
            event_type = data["Event"]

            media_details = self.extract_media_details(media, series, media_type)
            user_details = self.extract_user_details(data["User"])
            session_details = self.extract_session_details(data["Session"])
            server_details = self.extract_server_details(data["Server"])

            result = {
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
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


    def get_file_id(self):
        """ Extracts the file ID from the payload. """
        media_sources = self.payload.get("Item", {}).get("MediaSources", [])
        for source in media_sources:
            if source.get("Protocol") == "File":
                return source.get("Id")
        return None


    async def handle_play_event(self):
        """ Processes 'Play' event and logs it. """
        media_details, username = self.log_media_details()
        if media_details:
            logger.info(f"Processing play event for {media_details} for user {username}")

        self.details = self.extract_details()
        await self.dispatch_embed()


    async def handle_item_added(self, file_id):
        """ Processes 'ItemAdded' event and caches it. """
        if not self.cache.is_duplicate(file_id):
            self.details = self.extract_details()
            self.cache.store_item_added(file_id, self.details)

            media_details, username = self.log_media_details()
            if media_details:
                logger.info(f"Storing ItemAdded event for {media_details} for user {username}")
        else:
            logger.info(f"Skipping duplicate ItemAdded for File Id {file_id} within 24h.")


    async def handle_item_updated(self, file_id):
        """ Processes 'ItemUpdated' event if there's a matching 'ItemAdded'. """
        cached_data = self.cache.get_item_added(file_id)
        if cached_data:
            self.details = self.extract_details()
            self.cache.update_item_added(file_id, self.details)

            media_details, username = self.log_media_details()
            if media_details:
                logger.info(f"Sending embed for {media_details} for user {username}")

            await self.dispatch_embed()
        else:
            logger.info(f"ItemUpdated received without prior ItemAdded for File Id {file_id}. Skipping.")


    def log_media_details(self):
        """ Extracts media details for logging. """
        media = self.payload.get("Item", {})
        media_type = media.get("Type", "Unknown")
        user = self.payload.get("User", {})
        username = user.get("Name", "Unknown User")

        if media_type == "Episode":
            title = media.get("SeriesName", "Unknown Show")
            episode_name = media.get("Name", "Unknown Episode")
            season = media.get("ParentIndexNumber")
            episode = media.get("IndexNumber")
            episode_info = f"S{season:02}E{episode:02}" if season and episode else "Unknown Episode"
            return f"{title} - {episode_name} ({episode_info})", username

        if media_type == "Movie":
            title = media.get("Name", "Unknown Movie")
            release_year = media.get("ProductionYear", "Unknown Year")
            return f"{title} ({release_year})", username

        title = media.get("Name", "Unknown Media")
        return f"{title} (Unknown Type)", username


    def is_blocked_media_type(self, media_type):
        if media_type in ["Person", "Folder", "Season", "Series"]:
            logger.info(f"Blocking webhook request for media type: {media_type}")
            return True
        return False

    def is_valid_item(self, file_id):
        if not file_id:
            logger.warning("No File ID found, skipping event.")
            return False
        return True

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")

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
            'MarkPlayed': JELLYFIN_PLAYING,
            'ItemUpdated': JELLYFIN_CONTENT
        }.get(self.details.get('event'), 'default_channel_id')

    def get_embed_color(self):
        return {
            'Play': 0x6c76cc,
            'Resume': 0xac10c4,
            'Pause': 0x6e0918,
            'MarkPlayed': 0x054017,
            'ItemUpdated': 0x1e90ff,
        }.get(self.details.get('event'), 0x000000)

    def generate_embed(self):  
        embed_color = self.get_embed_color()
        return {
            'Play': self.embed_for_playing,
            'Resume': self.embed_for_resuming,
            'Pause': self.embed_for_pausing,
            'MarkPlayed': self.embed_for_markplayed,
            'ItemUpdated': self.embed_for_newcontent
        }.get(self.details.get('event'), lambda _: None)(embed_color)

    def embed_for_playing(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        trakt_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'Trakt'), None)
        embed = EmbedBuilder(title=title, url=trakt_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])
            
        embed.add_field(name="User", value=self.details['user']['username'], inline=True)
        embed.add_field(name="Method", value=self.details['session']['play_method'], inline=True)
        embed.add_field(name="Client", value=self.details['session']['client'], inline=True)

        embed.set_author(name="Jellyfin: Media Playing", icon_url=JELLYFIN_ICON)

        return embed
    
    def embed_for_resuming(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        trakt_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'Trakt'), None)
        embed = EmbedBuilder(title=title, url=trakt_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])
            
        embed.add_field(name="User", value=self.details['user']['username'], inline=True)
        embed.add_field(name="Method", value=self.details['session']['play_method'], inline=True)
        embed.add_field(name="Client", value=self.details['session']['client'], inline=True)
        
        embed.set_author(name="Jellyfin: Media Resumed", icon_url=JELLYFIN_ICON)

        return embed
    
    def embed_for_pausing(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        trakt_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'Trakt'), None)
        embed = EmbedBuilder(title=title, url=trakt_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])
            
        embed.add_field(name="User", value=self.details['user']['username'], inline=True)
        embed.add_field(name="Method", value=self.details['session']['play_method'], inline=True)
        embed.add_field(name="Client", value=self.details['session']['client'], inline=True)

        embed.set_author(name="Jellyfin: Media Paused", icon_url=JELLYFIN_ICON)

        return embed
    
    def embed_for_markplayed(self, color):
        media = self.details['media']
        title = self.format_media_title(media)

        trakt_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'Trakt'), None)
        embed = EmbedBuilder(title=title, url=trakt_url, color=color)

        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])
            
        embed.add_field(name="User", value=self.details['user']['username'], inline=True)
        embed.add_field(name="Method", value=self.details['session']['play_method'], inline=True)
        embed.add_field(name="Client", value=self.details['session']['client'], inline=True)

        embed.set_author(name="Jellyfin: Media Finished", icon_url=JELLYFIN_ICON)

        return embed

    def embed_for_newcontent(self, color):
        media = self.details['media']
        title = self.format_media_title(media)
        trakt_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'Trakt'), None)
        embed = EmbedBuilder(title=title, url=trakt_url, color=color)

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
            
        embed.set_author(name=f"Jellyfin: New {media['type']} added", icon_url=JELLYFIN_ICON)
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