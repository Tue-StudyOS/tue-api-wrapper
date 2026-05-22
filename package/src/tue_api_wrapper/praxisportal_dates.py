from __future__ import annotations

from datetime import datetime

from .config import GERMAN_TIMEZONE


def iso_from_timestamp(value: object, *, milliseconds: bool = False) -> str | None:
    if value in (None, "", 0):
        return None
    try:
        stamp = float(value)
    except (TypeError, ValueError):
        return None
    if milliseconds:
        stamp /= 1000
    return datetime.fromtimestamp(stamp, tz=GERMAN_TIMEZONE).isoformat()
