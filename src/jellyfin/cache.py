import time
from utils.custom_logger import logger

class EventCache:
    def __init__(self):
        self.item_cache = {}  # Stores temporary ItemAdded events
        self.name_cache = {}  # Tracks media names to avoid duplicate processing

    def is_duplicate(self, media_name, expiry=86400):
        """Check if an event is a duplicate within the given time frame."""
        current_time = time.time()
        if media_name in self.name_cache:
            last_updated = self.name_cache[media_name]
            if current_time - last_updated < expiry:
                return True
        self.name_cache[media_name] = current_time
        return False

    def store_item_added(self, item_id, data):
        """Store an ItemAdded event in the cache."""
        self.item_cache[item_id] = {
            "timestamp": time.time(),
            "data": data
        }
        logger.info(f"Stored ItemAdded event for ID {item_id}.")

    def get_item_added(self, item_id):
        """Retrieve and remove an ItemAdded event from the cache."""
        return self.item_cache.pop(item_id, None)

    def cleanup(self, item_max_age=300, name_max_age=86400):
        """Remove old entries from caches based on different expiration times."""
        current_time = time.time()

        # Clean up item_cache (ItemAdded events)
        expired_items = [key for key, value in self.item_cache.items() if current_time - value["timestamp"] > item_max_age]
        for key in expired_items:
            del self.item_cache[key]
            logger.info(f"Removed expired ItemAdded event from cache: {key}")

        # Clean up name_cache (Duplicate check)
        expired_names = [key for key, value in self.name_cache.items() if current_time - value > name_max_age]
        for key in expired_names:
            del self.name_cache[key]
            logger.info(f"Removed expired name cache entry: {key}")