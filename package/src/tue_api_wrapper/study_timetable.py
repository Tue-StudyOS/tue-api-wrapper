"""Bounded timetable observations using the original iCalendar event UID."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any
from zoneinfo import ZoneInfo

from .portal_common import current_dashboard_term


def _key(*parts: str) -> str:
    return sha256("\0".join(parts).encode()).hexdigest()


def collect_timetable(alma: Any, *, term: str | None, days: int, limit: int,
                      now: datetime | None = None) -> dict[str, Any]:
    if days < 1 or limit < 1:
        raise ValueError("days and limit must be positive")
    zone = ZoneInfo("Europe/Berlin")
    start = (now or datetime.now(zone)).astimezone(zone)
    end = start + timedelta(days=days)
    timetable = alma.timetable(term or current_dashboard_term(start.date()))
    events = sorted((e for e in timetable.occurrences if start <= e.start < end), key=lambda e: e.start)
    identities = [(e.uid or e.summary, e.start.astimezone(zone).date().isoformat()) for e in events]
    counts = Counter(identities)
    items = []
    for event, identity in list(zip(events, identities))[:limit]:
        ambiguous = counts[identity] > 1
        item = {
            "id": _key(timetable.term_label, *identity, event.start.isoformat() if ambiguous else ""),
            "title": event.summary, "start": event.start.isoformat(),
            "end": event.end.isoformat() if event.end else None,
            "location": event.location, "description": event.description,
        }
        if event.status is not None:
            item.update(status=event.status, cancellation_reason=event.cancellation_reason)
        items.append(item)
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("Timetable has indistinguishable occurrences")
    return {"status": "ok", "items": items, "coverage": "bounded", "term": timetable.term_label,
            "window_start": start.isoformat(), "window_end": end.isoformat(),
            "truncated": len(events) > limit,
            "identity_warning": any(not e.uid for e in events) or any(n > 1 for n in counts.values())}
