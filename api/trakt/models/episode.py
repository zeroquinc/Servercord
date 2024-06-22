from api.tmdb.client import TMDb

class Episode:
    def __init__(self, data):
        self.title = data['episode']['title']
        self.show_title = data['show']['title']
        self.season_number = data['episode']['season']
        self.episode_number = data['episode']['number']
        self.season_id = "{:02}".format(data['episode']['season'])  # Format as two-digit number
        self.episode_id = "{:02}".format(data['episode']['number'])  # Format as two-digit number
        self.year = data['show']['year']
        self.slug = data['show']['ids']['slug']
        self.trakt_id = data['show']['ids']['trakt']
        self.imdb_id = data['show']['ids']['imdb']
        self.tmdb_id = data['show']['ids']['tmdb']
        self.tvdb_id = data['show']['ids']['tvdb']
        self.url = f"https://trakt.tv/shows/{self.slug}/seasons/{self.season_number}/episodes/{self.episode_number}"
        self.poster = TMDb.show_poster_path(self.tvdb_id)