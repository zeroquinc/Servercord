from api.tmdb.client import TMDb

class Movie:
    def __init__(self, data):
        self.title = data['movie']['title']
        self.year = data['movie']['year']
        self.slug = data['movie']['ids']['slug']
        self.trakt_id = data['movie']['ids']['trakt']
        self.imdb_id = data['movie']['ids']['imdb']
        self.tmdb_id = data['movie']['ids']['tmdb']
        self.poster = TMDb.movie_poster_path(self.tmdb_id)