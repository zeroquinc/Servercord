from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger
from utils.formatter import Formatter
from utils.converter import Converter
from config.globals import RADARR_ICON

async def process_webhook(handler, channel):
    def build_grab_embed():
        embed = EmbedBuilder(title=handler.embed_title, color=0x9e7a18)
        embed.set_author(name=f"{handler.instance_name} - {handler.event_type}", icon_url=RADARR_ICON)
        embed.set_thumbnail(url=handler.poster)
        fields = {
            "Quality": (handler.quality, True),
            "Size": (Converter.bytes_to_human_readable(handler.size), True),
            "Indexer": (Formatter.indexer_value(handler.indexer), True),
            "Release": (handler.release_title, False),
            "Custom Formats": (Formatter.format_custom_formats(handler.custom_format_score, handler.custom_formats), False),
        }
        for name, (value, inline) in fields.items():
            embed.add_field(name=name, value=value, inline=inline)
        return embed

    def build_download_embed():
        embed = EmbedBuilder(description="A download event has occurred.")
        return embed

    def build_application_update_embed():
        embed = EmbedBuilder(title=handler.embed_title)
        embed.add_field(name="Old Version", value=handler.old_version, inline=True)
        embed.add_field(name="New Version", value=handler.new_version, inline=True)
        embed.set_author(name=f"{handler.instance_name} - {handler.event_type}", icon_url=RADARR_ICON)
        return embed

    def build_test_embed():
        embed = EmbedBuilder(description=f"This is a test event from {handler.instance_name}, it was a success!", color=0x9e7a18)
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