from src.discord.embed import EmbedBuilder
from utils.custom_logger import logger

async def process_webhook(handler, channel):
    def build_grab_embed():
        embed = EmbedBuilder(description="A grab event has occurred.")
        return embed

    def build_download_embed():
        embed = EmbedBuilder(description="A download event has occurred.")
        return embed

    def build_application_update_embed():
        embed = EmbedBuilder(description="An application update event has occurred.")
        return embed

    def build_test_embed():
        embed = EmbedBuilder(description="A test event has occurred.")
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