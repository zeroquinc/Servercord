from aiohttp import web

from utils.custom_logger import logger
from api.sonarr.client import SonarrWebhookHandler
from api.radarr.client import RadarrWebhookHandler
from api.plex.client import PlexWebhookHandler

class HandleWebHook:
    # Initialize the webhook receiver
    def __init__(self, discord_bot, host="0.0.0.0", port=2024):
        self.discord_bot = discord_bot
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_post('/sonarr_webhook', self.handle_webhook(SonarrWebhookHandler))
        self.app.router.add_post('/radarr_webhook', self.handle_webhook(RadarrWebhookHandler))
        self.app.router.add_post('/plex_webhook', self.handle_webhook(PlexWebhookHandler))
        self.uvicorn_params = {
            "host": self.host,
            "port": self.port,
            "access_log": False,
        }

    # Handle webhook
    def handle_webhook(self, Handler):
        async def handler(request):
            try:
                payload = await request.json()
                handler = Handler(payload, self.discord_bot)
                await handler.handle_webhook()
            except Exception as e:
                logger.error(f"Error handling webhook: {e}")
                return web.Response(text='Error', status=500)

            return web.Response(text='OK')
        return handler

    # Start the webhook receiver
    async def start(self):
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            logger.info(f"Server started at http://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error starting the server: {e}")

    # Cleanup the webhook receiver
    async def cleanup(self):
        await self.app.cleanup()