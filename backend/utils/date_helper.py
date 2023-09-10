from datetime import datetime
from typing import List


def get_latest_iso_datetime(iso_datetime_list: List[str]):
    latest_date = None
    for date_str in iso_datetime_list:
        date = datetime.fromisoformat(date_str)
        if latest_date is None or date > latest_date:
            latest_date = date

    return latest_date.isoformat() + "Z" if latest_date else None


def get_current_iso_datetime():
    # Get current date and time in UTC
    now = datetime.utcnow()

    # Format the datetime in ISO UTC format
    iso_utc_datetime = now.isoformat(timespec="seconds") + "Z"

    return iso_utc_datetime


def get_today_iso_date():
    # Get current date and time in UTC
    now = datetime.utcnow()

    # Set the time to midnight
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Format the date in ISO UTC format
    iso_utc_midnight = midnight.isoformat(timespec="seconds") + "Z"

    return iso_utc_midnight
