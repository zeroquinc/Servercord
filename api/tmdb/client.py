import requests

from config.globals import TMDB_API_KEY
from utils.custom_logger import logger

class TMDb:
    BASE_URL = "https://api.themoviedb.org/3"
    API_KEY = TMDB_API_KEY

    # Fetches the show poster path from TMDb
    @classmethod
    def show_poster_path(cls, tvdb_id):
        try:
            response = requests.get(
                f"{cls.BASE_URL}/find/{tvdb_id}",
                params={
                    "api_key": cls.API_KEY,
                    "external_source": "tvdb_id"
                }
            )
            response.raise_for_status()
            data = response.json()
            if (tv_results := data.get('tv_results', [])):
                return f"https://image.tmdb.org/t/p/original{tv_results[0].get('poster_path')}"
        except Exception as e:
            logger.error(f"Failed to fetch show poster path from TMDb: {e}")
        return None

    # Fetches the movie poster path from TMDb
    @classmethod
    def movie_poster_path(cls, tmdb_id):
        try:
            response = requests.get(
                f"{cls.BASE_URL}/movie/{tmdb_id}",
                params={"api_key": cls.API_KEY}
            )
            response.raise_for_status()
            data = response.json()
            return f"https://image.tmdb.org/t/p/original{data.get('poster_path')}"
        except Exception as e:
            logger.error(f"Failed to fetch movie poster path from TMDb: {e}")
        return None