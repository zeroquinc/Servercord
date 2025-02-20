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
        """Extracts relevant details from the Jellyfin webhook payload."""
        try:
            logger.debug("Extracting details from Jellyfin payload.")
            
            event = self.payload.get("Event", "Unknown Event")
            item = self.payload.get("Item", {})
            user = self.payload.get("User", {})
            session = self.payload.get("Session", {})
            server = self.payload.get("Server", {})
            series = self.payload.get("Series", {})

            # Extract media details
            media_type = item.get("Type", "Unknown")  # Movie, Episode, etc.
            name = item.get("Name", "Unknown")
            overview = item.get("Overview", "No overview available.")
            file_path = item.get("Path", "Unknown path")
            official_rating = item.get("OfficialRating", "Not Rated")
            genres = item.get("Genres", [])
            community_rating = item.get("CommunityRating", "N/A")
            production_year = item.get("ProductionYear", "N/A")
            premiere_date = item.get("PremiereDate", "N/A")
            is_hd = item.get("IsHD", False)
            runtime_ticks = item.get("RunTimeTicks", 0)
            critic_rating = item.get("CriticRating", "N/A")
            production_locations = item.get("ProductionLocations", [])
            taglines = item.get("Taglines", [])
            remote_trailers = item.get("RemoteTrailers", [])
            media_provider_ids = item.get("ProviderIds", {})  # ProviderIds for the media itself
            external_urls = item.get("ExternalUrls", [])  # External URLs for the Movie (e.g., IMDb, TMDb)

            if media_type == "Episode":
                poster_url = TMDb.show_poster_path(series.get("ProviderIds", {}).get("Tvdb", "N/A"))
            else:
                poster_url = TMDb.movie_poster_path(media_provider_ids.get("Tmdb", "N/A"))

            # Convert runtime to seconds
            runtime_seconds = runtime_ticks / 10_000_000 if runtime_ticks else 0

            # Extract user details
            username = user.get("Name", "Unknown User")
            user_id = user.get("Id", "Unknown ID")
            is_admin = user.get("Policy", {}).get("IsAdministrator", False)
            last_login = user.get("LastLoginDate", "Unknown")

            # Extract session details
            device_name = session.get("DeviceName", "Unknown Device")
            client = session.get("Client", "Unknown Client")
            remote_ip = session.get("RemoteEndPoint", "Unknown IP")
            is_paused = session.get("PlayState", {}).get("IsPaused", False)

            # Extract server details
            server_name = server.get("Name", "Unknown Server")
            server_version = server.get("Version", "Unknown Version")

            # Initialize media details based on type
            media_details = {
                "type": media_type,  # Movie, Episode, etc.
                "name": name,
                "overview": overview,
                "file_path": file_path,
                "official_rating": official_rating,
                "genres": genres,
                "community_rating": community_rating,
                "production_year": production_year,
                "premiere_date": premiere_date,
                "is_hd": is_hd,
                "runtime_seconds": runtime_seconds,
                "provider_ids": media_provider_ids,  # Add ProviderIds for the media itself
                "external_urls": external_urls,  # Add External URLs for the media
                "poster_url": poster_url
            }

            # Movie-specific fields
            if media_type == "Movie":
                media_details.update({
                    "critic_rating": critic_rating,
                    "production_locations": production_locations,
                    "taglines": taglines,
                    "remote_trailers": remote_trailers
                })

            elif media_type == "Episode":
                # For episodes, include season and episode
                season = item.get("ParentIndexNumber", "N/A")
                episode = item.get("IndexNumber", "N/A")
                media_details.update({
                    "season": season,
                    "episode": episode,
                })

                # Also include series details for episodes
                series_name = series.get("Name", "Unknown Series")
                series_overview = series.get("Overview", "No series overview available.")
                series_rating = series.get("CommunityRating", "N/A")
                media_details["series"] = {
                    "name": series_name,
                    "overview": series_overview,
                    "community_rating": series_rating,
                    "provider_ids": series.get("ProviderIds", {}),  # Add ProviderIds for Series
                    "premiere_date": series.get("PremiereDate", "Unknown"),
                    "external_urls": series.get("ExternalUrls", [])  # Add External URLs for Series (Trakt, IMDb, etc.)
                }

            # Extract user details (same for all media types)
            user_details = {
                "username": username,
                "user_id": user_id,
                "is_admin": is_admin,
                "last_login": last_login
            }

            # Extract session details (same for all media types)
            session_details = {
                "device_name": device_name,
                "client": client,
                "remote_ip": remote_ip,
                "is_paused": is_paused
            }

            # Extract server details (same for all media types)
            server_details = {
                "server_name": server_name,
                "server_version": server_version
            }

            details = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "media": media_details,
                "user": user_details,
                "session": session_details,
                "server": server_details
            }

            return details

        except Exception as e:
            logger.error(f"Error extracting details: {e}")
            return {}

    async def handle_webhook(self):
        logger.info(f"Processing Jellyfin webhook payload for event type: {self.details['event']}")
        logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")
        logger.debug(f"Details: {json.dumps(self.details, indent=4)}")
        await self.dispatch_embed()

    def determine_channel_id(self):
        channel_ids = {
            'Play': JELLYFIN_PLAYING,
            'ItemAdded': JELLYFIN_CONTENT,
        }
        return channel_ids.get(self.details['event'], 'default_channel_id')

    def get_embed_color(self):
        color_mapping = {
            'Play': 0x6c76cc,           # Purpleish color for now playing
            'ItemAdded': 0x1e90ff   # Blue color for new episode content
        }
        return color_mapping.get(self.details['event'], 0x000000)  # Default to black if not found

    def generate_embed(self):
        embed_color = self.get_embed_color()  # Get color based on webhook type

        embed_creators = {
            'Play': self.embed_for_playing,
            'ItemAdded': self.embed_for_newcontent,
        }
        return embed_creators.get(self.details['event'])(embed_color)

    def embed_for_playing(self, color):
        media = self.details['media']
        if media['type'] == "Movie":
            title = f"{media['name']} ({media['production_year']})"
        elif media['type'] == "Episode":
            season = f"S{int(media.get('season', 0)):02}"
            episode = f"E{int(media.get('episode', 0)):02}"
            title = f"{media['series']['name']} ({season}{episode})"
        else:
            title = f"{media['name']} (Unknown Type)"

        imdb_url = next((url['Url'] for url in self.details['media']['external_urls'] if url['Name'] == 'IMDb'), None)
        embed = EmbedBuilder(title=title, url=imdb_url, color=color)

        if media['poster_url']:
            embed.set_thumbnail(url=media['poster_url'])

        embed.set_author(name="Now Playing on Jellyfin", icon_url=JELLYFIN_ICON)
        embed.set_footer(text=f"{self.details['user']['username']} • {self.details['session']['client']}")

        return embed

    def embed_for_newcontent(self, color):
        embed = EmbedBuilder(title=self.get_newcontent_title(), url=self.plex_url, color=color)
        if self.summary:
            if self.details['event'] in ['newcontent_episode', 'newcontent_season']:
                embed.add_field(name="Plot", value=f"||{self.summary}||", inline=False)
            else:
                embed.add_field(name="Plot", value=self.summary, inline=False)
        if self.poster_url:
            embed.set_thumbnail(url=self.poster_url)
        if self.details['event'] == 'newcontent_episode':
            embed.set_footer(text=f"Aired on {self.air_date}")
        elif self.details['event'] == 'newcontent_season':
            embed.add_field(name="Episodes", value=f"{self.episode_count}", inline=False)
        elif self.details['event'] == 'newcontent_movie':
            links = self.build_links()
            if links:
                embed.add_field(name="Links", value=links, inline=False)
            footer_text = self.build_footer()
            embed.set_footer(text=footer_text)
        embed.set_author(name=f"New {self.media_type.capitalize()} added to Plex", icon_url=PLEX_ICON)
        return embed

    def get_newcontent_title(self):
        titles = {
            'newcontent_episode': f"{self.title} (S{self.season_num00}E{self.episode_num00})",
            'newcontent_season': f"{self.title}",
            'newcontent_movie': f"{self.title} ({self.year})"
        }
        return titles.get(self.details['event'], self.title)
    
    def build_links(self):
        links = []
        if self.imdb_url and self.imdb_url.lower() != "n/a":
            links.append(f"[IMDb]({self.imdb_url})")
        if self.tmdb_url and self.tmdb_url.lower() != "n/a":
            links.append(f"[TMDb]({self.tmdb_url})")
        if self.tmdb_id_plex:
            links.append(f"[Trakt](https://trakt.tv/search/imdb?query={self.tmdb_id_plex})")
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