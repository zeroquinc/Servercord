from datetime import datetime, timedelta

def get_times():
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1200)
    return now, one_hour_ago