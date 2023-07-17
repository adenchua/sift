from datetime import datetime


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
