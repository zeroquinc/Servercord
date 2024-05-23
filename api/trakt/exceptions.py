class TraktAPIException(Exception):
    def __init__(self, error_data):
        self.status_code = error_data.get('status_code')
        self.message = error_data.get('message')
        super().__init__(self.message)