from api.trakt.models.show import Show

class Shows:
    def __init__(self, client):
        self.client = client

    def _get_show_list(self, endpoint):
        params = {}
        response = self.client._get(endpoint, params=params)
        return [Show(show) for show in response]

    def get_popular(self):
        endpoint = 'shows/popular'
        return [Show(show) for show in self.client._get(endpoint)]

    def get_trending(self):
        endpoint = 'shows/trending'
        return self._get_show_list(endpoint)