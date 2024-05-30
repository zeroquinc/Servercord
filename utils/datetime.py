from datetime import datetime, timedelta

class TimeCalculator:
    @staticmethod
    def get_time_ago(hours=0, minutes=0):
        now = datetime.now()
        time_ago = now - timedelta(hours=hours, minutes=minutes)
        return now, time_ago
    
    @staticmethod
    def seconds_until_next_hour():
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        delta = next_hour - now
        return delta.seconds

    @staticmethod
    def seconds_until_next_day():
        now = datetime.now()
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        delta = next_day - now
        return delta.seconds