from loguru import logger
from datetime import datetime
import logging
import json
from pathlib import Path
import sys
from config.config import LOG_LEVEL

discord_logger = None

def create_logger():
    logs_path = Path('logs')
    logs_path.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    # Correct format string - ANSI codes REMOVED:
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}</cyan> | <yellow>{function}</yellow> | <cyan>{module}</cyan> | <level>{message}</level>" # % removed

    logger.add(
        logs_path / f"{today}-servercord.log",
        level=LOG_LEVEL,
        format=log_format,
        # colorize=True,  # Add this back if you want loguru to handle colors. Remove for plain text
    )
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format=log_format,
        colorize=True, # Colorize for console output
    )

def switch_logger():
    """
    Switches the logger configuration based on the log level.

    Args:
        None

    Returns:
        None

    Raises:
        ValueError: If the log level is invalid
    """
    logger.remove()
    if LOG_LEVEL in ['DEBUG', 'INFO']:
        create_logger()
    else:
        raise ValueError("Invalid log level")

def log_json(json_obj, level='DEBUG'):
    """
    Logs a JSON object with the specified log level.

    Args:
        json_obj (dict): The JSON object to log.
        level (str): The log level to use. Defaults to 'DEBUG'.

    Returns:
        None

    Raises:
        None
    """
    pretty_json = json.dumps(json_obj, indent=4)
    logger.log(level, pretty_json)

def setup_discord_logging():
    """
    Sets up logging for the 'discord' logger with a custom DiscordHandler.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """
    global discord_logger
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)
    discord_handler = DiscordHandler()
    discord_logger.handlers = [discord_handler]
    discord_logger.propagate = False

class DiscordHandler(logging.Handler):
    """
    Custom logging handler for Discord, emits log records to the logger and Discord.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """
    def emit(self, record):
        log_entry = self.format(record)
        logger.log(record.levelno, log_entry)
        if len(discord_logger.handlers) > 1:
            discord_logger.handlers = [self]

switch_logger()
setup_discord_logging()