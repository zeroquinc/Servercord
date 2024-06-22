from dateutil.parser import parse
from dateutil.tz import tzlocal

from api.tmdb.client import TMDb

class Rating:
    def __init__(self, data):
        self.type = data['type']
        self.rated = data['rating']
        self.rated_at = parse(data['rated_at']).astimezone(tzlocal())  # Convert to local timezone
        self.date = self.rated_at.strftime("%d/%m/%Y %H:%M:%S")  # Convert to human readable format
        self.show_title = None
        self.season_id = None
        self.episode_id = None
        self.trakt_id = None
        self.imdb_id = None
        self.tmdb_id = None
        self.tvdb_id = None
        self.poster = None
        self.slug = None
        media = create_media(data)
        self.set_media_attributes(media)

    def set_media_attributes(self, media):
        self.title = media.title
        self.year = media.year
        self.poster = media.poster
    
        if isinstance(media, (Episode, Season)):
            self.show_title = media.show_title
            self.season_id = media.season_id
    
        if isinstance(media, Episode):
            self.episode_id = media.episode_id

    @classmethod
    def from_json(cls, data):
        return cls(data)

def create_media(data):
    media_classes = {'movie': Movie, 'episode': Episode, 'season': Season, 'show': Show}
    media_type = data['type']
    return media_classes.get(media_type, lambda _: None)(data)

class Movie:
    def __init__(self, data):
        self.title = data['movie']['title']
        self.year = data['movie']['year']
        self.slug = data['movie']['ids']['slug']
        self.trakt_id = data['movie']['ids']['trakt']
        self.imdb_id = data['movie']['ids']['imdb']
        self.tmdb_id = data['movie']['ids']['tmdb']
        self.poster = TMDb.movie_poster_path(self.tmdb_id)

class Episode:
    def __init__(self, data):
        self.title = data['episode']['title']
        self.show_title = data['show']['title']
        self.season_id = "{:02}".format(data['episode']['season'])  # Format as two-digit number
        self.episode_id = "{:02}".format(data['episode']['number'])  # Format as two-digit number
        self.year = data['show']['year']
        self.slug = data['show']['ids']['slug']
        self.trakt_id = data['show']['ids']['trakt']
        self.imdb_id = data['show']['ids']['imdb']
        self.tmdb_id = data['show']['ids']['tmdb']
        self.tvdb_id = data['show']['ids']['tvdb']
        self.poster = TMDb.show_poster_path(self.tvdb_id)

class Season:
    def __init__(self, data):
        self.title = data['show']['title']
        self.show_title = data['show']['title']
        self.season_id = "{:02}".format(data['season']['number'])  # Format as two-digit number
        self.year = data['show']['year']
        self.slug = data['show']['ids']['slug']
        self.trakt_id = data['show']['ids']['trakt']
        self.imdb_id = data['show']['ids']['imdb']
        self.tmdb_id = data['show']['ids']['tmdb']
        self.tvdb_id = data['show']['ids']['tvdb']
        self.poster = TMDb.show_poster_path(self.tvdb_id)

class Show:
    def __init__(self, data):
        self.show_title = data['show']['title']
        self.year = data['show']['year']
        self.slug = data['show']['ids']['slug']
        self.trakt_id = data['show']['ids']['trakt']
        self.imdb_id = data['show']['ids']['imdb']
        self.tmdb_id = data['show']['ids']['tmdb']
        self.tvdb_id = data['show']['ids']['tvdb']
        self.poster = TMDb.show_poster_path(self.tvdb_id)