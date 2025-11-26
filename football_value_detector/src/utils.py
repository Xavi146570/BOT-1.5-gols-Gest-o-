# src/utils.py
import datetime

def get_utc_today_plus_days(days: int = 0) -> datetime.date:
    return (datetime.datetime.utcnow() + datetime.timedelta(days=days)).date()
