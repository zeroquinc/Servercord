from loguru import logger
from datetime import datetime
import logging
import json
from pathlib import Path
import sys
from config.config import LOG_LEVEL

discord_logger = None

def create_logger():
    """Creates and configures the logger."""
    logs_path = Path('logs')
    logs_path.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    script_dir = Path(__file__).parent  # Or Path('.').resolve()
    script_dir_str = str(script_dir)

    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}</cyan> | <yellow>{function}</yellow> | <magenta>{extra[script_dir]}</magenta> | <level>{message}</level>"

    # Use a lambda function to inject the extra data *into the message*
    def filter_(record):
        record["extra"]["script_dir"] = script_dir_str  # Add to record's extra
        return True # Keep all messages

    logger.add(
        logs_path / f"{today}-servercord.log",
        level=LOG_LEVEL,
        colorize=True,
        format=log_format,
        filter=filter_  # Apply the filter
    )
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        colorize=True,
        format=log_format,
        filter=filter_  # Apply the filter
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