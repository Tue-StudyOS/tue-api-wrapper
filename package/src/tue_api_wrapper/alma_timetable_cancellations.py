from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, datetime, time

from bs4 import BeautifulSoup

from .alma_timetable_html import _parse_day_date
from .alma_timetable_rooms import _field_text, _key, _text, _time_range
from .config import GERMAN_TIMEZONE
from .models import CalendarEvent, CalendarOccurrence

_Slot = tuple[str, datetime, datetime | None]


def apply_timetable_cancellations(
    occurrences: tuple[CalendarOccurrence, ...],
    html: str,
    events: tuple[CalendarEvent, ...],
) -> tuple[CalendarOccurrence, ...]:
    cancellations = {_slot(item): item for item in _cancelled_occurrences(html)}
    if not cancellations:
        return occurrences

    # Alma may omit the instance from the feed using EXDATE. Only restore it
    # when the dated timetable column explicitly identifies a cancellation.
    updated = []
    for occurrence in occurrences:
        cancellation = cancellations.pop(_slot(occurrence), None)
        if cancellation is not None:
            occurrence = replace(
                occurrence,
                status=cancellation.status,
                cancellation_reason=cancellation.cancellation_reason,
            )
        updated.append(occurrence)
    sources = _excluded_slots(events)
    for slot, cancellation in cancellations.items():
        source = sources.get(slot)
        if source is not None:
            cancellation = replace(cancellation, uid=source.uid, description=source.description)
        updated.append(cancellation)
    return tuple(sorted(updated, key=lambda item: (item.start, item.summary.casefold())))


def _slot(item: CalendarOccurrence) -> _Slot:
    return _key(item.summary), item.start, item.end


def _excluded_slots(events: tuple[CalendarEvent, ...]) -> dict[_Slot, CalendarEvent | None]:
    slots: dict[_Slot, CalendarEvent | None] = {}
    for event in events:
        if not isinstance(event.start, datetime) or not isinstance(event.end, datetime):
            continue
        duration = event.end - event.start
        for start in event.excluded_starts:
            if isinstance(start, datetime):
                slot = (_key(event.summary), start, start + duration)
                slots[slot] = None if slot in slots else event
    return slots


def _cancelled_occurrences(html: str) -> Iterator[CalendarOccurrence]:
    soup = BeautifulSoup(html, "html.parser")
    for column in soup.select("div.planFrame > ul.plan > li.column"):
        title = _text(column.select_one(".colhead h2"))
        iso_day = _parse_day_date(title or "")
        if iso_day is None:
            continue
        day = date.fromisoformat(iso_day)
        for panel in column.select('li.scheduleCancelled > div[id$=":scheduleItem:schedulePanelGroup"]'):
            summary = _text(panel.select_one("h3.scheduleTitle"))
            start, end = _time_range(_field_text(panel, "processingTimes"))
            if not summary or start is None or end is None:
                continue
            yield CalendarOccurrence(
                summary=summary,
                start=datetime.combine(day, time.fromisoformat(start), GERMAN_TIMEZONE),
                end=datetime.combine(day, time.fromisoformat(end), GERMAN_TIMEZONE),
                location=None,
                description=None,
                status="cancelled",
                cancellation_reason=_text(panel.select_one(".errortextPlan .fieldsetMessageText")),
            )
