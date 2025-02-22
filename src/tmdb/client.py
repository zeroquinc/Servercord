import requests
from config.globals import TMDB_API_KEY
from utils.custom_logger import logger

class TMDb:
    BASE_URL = "https://api.themoviedb.org/3"
    API_KEY = TMDB_API_KEY

    _cache = {}  # Dictionary to store cached results

    @classmethod
    def show_poster_path(cls, tvdb_id):
        cache_key = f"tv_{tvdb_id}"
        if cache_key in cls._cache:
            logger.debug(f"Found show poster path in cache for {tvdb_id}")
            return cls._cache[cache_key]

        try:
            response = requests.get(
                f"{cls.BASE_URL}/find/{tvdb_id}",
                params={"api_key": cls.API_KEY, "external_source": "tvdb_id"}
            )
            response.raise_for_status()
            data = response.json()
            if (tv_results := data.get('tv_results', [])):
                poster_path = f"https://image.tmdb.org/t/p/original{tv_results[0].get('poster_path')}"
                cls._cache[cache_key] = poster_path  # Store in cache
                return poster_path
        except Exception as e:
            logger.error(f"Failed to fetch show poster path from TMDb: {e}")

        return None

    @classmethod
    def movie_poster_path(cls, tmdb_id):
        cache_key = f"movie_{tmdb_id}"
        if cache_key in cls._cache:
            logger.debug(f"Found movie poster path in cache for {tmdb_id}")
            return cls._cache[cache_key]

        try:
            response = requests.get(
                f"{cls.BASE_URL}/movie/{tmdb_id}",
                params={"api_key": cls.API_KEY}
            )
            response.raise_for_status()
            data = response.json()
            poster_path = f"https://image.tmdb.org/t/p/original{data.get('poster_path')}"
            cls._cache[cache_key] = poster_path  # Store in cache
            return poster_path
        except Exception as e:
            logger.error(f"Failed to fetch movie poster path from TMDb: {e}")

        return None