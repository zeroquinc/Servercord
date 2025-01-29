from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger
from utils.formatter import Formatter
from utils.converter import Converter
from config.globals import SONARR_ICON

from utils.custom_logger import logger

async def process_webhook(handler, channel):
    def build_grab_embed():
        embed = EmbedBuilder(title=handler.embed_title, description=f"```{handler.release_title}```", color=0x9e7a18)
        embed.add_field(name="Custom Formats", value=f"```{Formatter.format_custom_formats(handler.custom_format_score, handler.custom_formats)}```", inline=False)
        embed.set_thumbnail(url=handler.poster)
        embed.set_author(name="A new grab by Sonarr", icon_url=SONARR_ICON)
        embed.set_footer(text=f"{handler.quality} • {Converter.bytes_to_human_readable(handler.size)} • {handler.indexer}")
        
        logger.info(f"Sending grab embed to Discord: {handler.release_title} - {handler.embed_title}")
        
        return embed

    def build_download_embed():
        embed = EmbedBuilder(description="A download event has occurred.")
        return embed

    def build_application_update_embed():
        embed = EmbedBuilder()
        embed.add_field(name="Old Version", value=handler.old_version, inline=True)
        embed.add_field(name="New Version", value=handler.new_version, inline=True)
        embed.set_author(name=f"{handler.instance_name} - {handler.event_type}", icon_url=SONARR_ICON)
        
        logger.info(f"Sending application update embed to Discord: {handler.instance_name} - {handler.event_type}")
        
        return embed

    def build_test_embed():
        embed = EmbedBuilder(description=f"This is a test event from {handler.instance_name}, it was a success!", color=0xadd9c9)
        
        logger.info(f"Sending test embed to Discord: {handler.instance_name}")
        
        return embed

    embed_builders = {
        'Grab': build_grab_embed,
        'Download': build_download_embed,
        'ApplicationUpdate': build_application_update_embed,
        'Test': build_test_embed,
    }

    if handler.event_type not in embed_builders:
        logger.error(f"Unknown event type: {handler.event_type}")
        return

    embed_builder = embed_builders[handler.event_type]()
    await embed_builder.send_embed(channel)