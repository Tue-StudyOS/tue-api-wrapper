from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

def current_dashboard_term(now: date | None = None) -> str:
    """University semester boundaries: https://uni-tuebingen.de/en/843."""
    today = now or datetime.now(ZoneInfo("Europe/Berlin")).date()
    if 4 <= today.month <= 9:
        return f"Sommer {today.year}"
    start = today.year - 1 if today.month < 4 else today.year
    return f"Winter {start}/{(start + 1) % 100:02d}"


DEFAULT_DASHBOARD_TERM = current_dashboard_term()
RELATIVE_DASHBOARD_TERMS = {
    "",
    "aktuell",
    "aktuelles semester",
    "current",
    "current semester",
    "current term",
    "default",
    "dieses semester",
    "this semester",
    "this term",
}


def normalize_dashboard_term(term_label: str | None = None) -> str:
    raw = (term_label or "").strip()
    key = " ".join(raw.casefold().replace("_", " ").replace("-", " ").split())
    return current_dashboard_term() if key in RELATIVE_DASHBOARD_TERMS else raw


def serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value
