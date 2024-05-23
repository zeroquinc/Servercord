from dateutil.parser import parse
from dateutil.tz import tzlocal

class Rating:
    def __init__(self, data):
        self.type = data['type']
        self.rated = data['rating']
        self.rated_at = parse(data['rated_at']).astimezone(tzlocal())  # Convert to local timezone
        self.show_title = None
        self.season_id = None
        self.episode_id = None
        media = create_media(data)
        self.set_media_attributes(media)

    def set_media_attributes(self, media):
        self.title = media.title
        self.year = media.year
    
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

class Episode:
    def __init__(self, data):
        self.title = data['episode']['title']
        self.show_title = data['show']['title']
        self.season_id = "{:02}".format(data['episode']['season'])  # Format as two-digit number
        self.episode_id = "{:02}".format(data['episode']['number'])  # Format as two-digit number
        self.year = data['show']['year']

class Season:
    def __init__(self, data):
        self.title = data['show']['title']
        self.show_title = data['show']['title']
        self.season_id = "{:02}".format(data['season']['number'])  # Format as two-digit number
        self.year = data['show']['year']

class Show:
    def __init__(self, data):
        self.title = data['show']['title']
        self.year = data['show']['year']