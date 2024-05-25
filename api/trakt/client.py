import requests
from config.globals import TRAKT_API_URL, TRAKT_CLIENT_ID
from .exceptions import TraktAPIException

class TraktClient:
    def __init__(self):
        self.client_id = TRAKT_CLIENT_ID
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": self.client_id
        }
        self.session.headers.update(self.headers)

    def _get(self, endpoint, params=None):
        url = f'{TRAKT_API_URL}/{endpoint}'
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            raise TraktAPIException(response.json())
        return response.json()

    def user(self, username):
        from .endpoints.user import User
        return User(self, username)

    def shows(self):
        from .endpoints.shows import Shows
        return Shows(self)