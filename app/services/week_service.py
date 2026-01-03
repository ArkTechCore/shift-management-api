# app/services/week_service.py

from datetime import date, timedelta


def get_week_start(any_date: date) -> date:
    """
    Returns the Friday of the week for any given date.
    """
    # Monday = 0 ... Sunday = 6
    weekday = any_date.weekday()

    # Friday = 4
    days_from_friday = (weekday - 4) % 7
    return any_date - timedelta(days=days_from_friday)


def get_week_end(week_start: date) -> date:
    """
    Returns Thursday for a given Friday.
    """
    return week_start + timedelta(days=6)
