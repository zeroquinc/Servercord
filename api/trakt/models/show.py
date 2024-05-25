from api.tmdb.client import TMDb

class Show:
    def __init__(self, data):
        show_data = data['show'] if 'show' in data else data
        self.title = show_data['title']
        self.year = show_data['year']
        self.slug = show_data['ids']['slug']
        self.trakt_id = show_data['ids']['trakt']
        self.imdb_id = show_data['ids']['imdb']
        self.tmdb_id = show_data['ids']['tmdb']
        self.tvdb_id = show_data['ids']['tvdb']
        self.poster = TMDb.show_poster_path(self.tvdb_id)