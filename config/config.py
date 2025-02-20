"""
Global config variables
"""

LOG_LEVEL = 'DEBUG'  # or 'DEBUG, WARNING, ERROR, CRITICAL'
DELAY_START = False # Set to True to delay the start of tasks

WEBHOOKS_ENABLED = {
    "sonarr": True,
    "radarr": True,
    "plex": False,
    "jellyfin": True,
}
