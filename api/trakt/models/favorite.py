from dateutil.parser import parse
from dateutil.tz import tzlocal

from api.trakt.models.movie import Movie
from api.trakt.models.show import Show
from api.trakt.models.season import Season
from api.trakt.models.episode import Episode

class Favorite:
    def __init__(self, data):
        self.type = data['type']
        self.listed_at = parse(data['listed_at']).astimezone(tzlocal())  # Convert to local timezone
        self.date = self.listed_at.strftime("%d/%m/%Y %H:%M:%S")  # Convert to human readable format
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
            
        if isinstance(media, Show):
            self.show_title = media.title

    @classmethod
    def from_json(cls, data):
        return cls(data)

def create_media(data):
    media_classes = {'movie': Movie, 'episode': Episode, 'season': Season, 'show': Show}
    media_type = data['type']
    return media_classes.get(media_type, lambda _: None)(data)