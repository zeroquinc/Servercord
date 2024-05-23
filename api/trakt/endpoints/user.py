from dateutil.parser import parse
from dateutil.tz import tzlocal

from api.trakt.models.rating import Rating
from api.trakt.models.favorite import Favorite

class User:
    def __init__(self, client, username):
        self.client = client
        self.username = username

    def convert_to_tz_aware(self, dt):
        return dt.replace(tzinfo=tzlocal()) if dt is not None else None

    def get_ratings(self, media_type="all", rating=None, start_time=None, end_time=None):
        endpoint = f'users/{self.username}/ratings/{media_type}'
        params = {}
        if rating:
            params['rating'] = rating

        ratings = self.client._get(endpoint, params=params)
        start_time = self.convert_to_tz_aware(start_time)
        end_time = self.convert_to_tz_aware(end_time)

        def is_within_time_range(rating_time):
            return (start_time is None or rating_time >= start_time) and (end_time is None or rating_time <= end_time)

        ratings = [Rating(rating) for rating in ratings if is_within_time_range(parse(rating['rated_at']).astimezone(tzlocal()))]

        return ratings
    
    def get_favorites(self, media_type="all", favorite=None, start_time=None, end_time=None):
        endpoint = f'users/{self.username}/favorites/{media_type}'
        params = {}
        if favorite:
            params['favorite'] = favorite

        favorites = self.client._get(endpoint, params=params)
        start_time = self.convert_to_tz_aware(start_time)
        end_time = self.convert_to_tz_aware(end_time)

        def is_within_time_range(rating_time):
            return (start_time is None or rating_time >= start_time) and (end_time is None or rating_time <= end_time)

        favorites = [Favorite(favorite) for favorite in favorites if is_within_time_range(parse(favorite['listed_at']).astimezone(tzlocal()))]

        return favorites