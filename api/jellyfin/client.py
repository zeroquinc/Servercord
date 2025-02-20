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
            logger.debug(f"Payload: {json.dumps(self.payload, indent=4)}")

            data = {k: self.payload.get(k, {}) for k in ["Event", "Item", "User", "Session", "Server", "Series"]}
            media = data["Item"]
            series = data["Series"]
            media_type = media.get("Type", "Unknown")

            media_details = self.extract_media_details(media, series, media_type)
            user_details = self.extract_user_details(data["User"])
            session_details = self.extract_session_details(data["Session"])
            server_details = self.extract_server_details(data["Server"])

            return {
                "event": data["Event"],
                "timestamp": datetime.utcnow().isoformat(),
                "media": media_details,
                "user": user_details,
                "session": session_details,
                "server": server_details,
            }

        except Exception as e:
            logger.error(f"Error extracting details: {e}")
            return {}

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
        logger.info(f"Processing Jellyfin webhook payload for event type: {self.details.get('event', 'Unknown Event')}")
        await self.dispatch_embed()  

    def determine_channel_id(self):
        return {
            'Play': JELLYFIN_PLAYING,
            'ItemAdded': JELLYFIN_CONTENT,
        }.get(self.details.get('event'), 'default_channel_id')

    def get_embed_color(self):
        return {
            'Play': 0x6c76cc,
            'ItemAdded': 0x1e90ff,
        }.get(self.details.get('event'), 0x000000)

    def generate_embed(self):  
        embed_color = self.get_embed_color()
        return {
            'Play': self.embed_for_playing,
            'ItemAdded': self.embed_for_newcontent
        }.get(self.details.get('event'), lambda _: None)(embed_color)

    def embed_for_playing(self, color):
        media = self.details['media']
        embed = EmbedBuilder(title=self.format_media_title(media), color=color)
        if media.get('poster_url'):
            embed.set_thumbnail(url=media['poster_url'])
        embed.set_author(name="Now Playing on Jellyfin", icon_url=JELLYFIN_ICON)
        return embed

    def embed_for_newcontent(self, color):
        media = self.details['media']
        title = self.get_newcontent_title(media)
        embed = EmbedBuilder(title=title, color=color)

        imdb_url = next((url['Url'] for url in media.get('external_urls', []) if url.get('Name') == 'IMDb'), None)
        if imdb_url:
            embed.set_title(title, url=imdb_url)
        else:
            embed.set_title(title)

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
            footer_parts.append(f"Premiered: {premiere_date}")

        # Add runtime if available
        if media.get("runtime_seconds"):
            duration = f"{int(media['runtime_seconds'] // 60)} min"
            footer_parts.append(duration)

        return " • ".join(footer_parts)

    async def dispatch_embed(self):
        embed = self.generate_embed()
        channel_id = self.determine_channel_id()
        channel = self.discord_bot.bot.get_channel(channel_id)
        if channel:
            await embed.send_embed(channel)
        else:
            logger.error(f"Channel with ID {channel_id} not found.")