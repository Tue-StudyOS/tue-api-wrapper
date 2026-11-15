from __future__ import annotations

from datetime import date, datetime, time, timezone
import re
from typing import Iterable
from zoneinfo import ZoneInfo

from dateutil import rrule

from .config import GERMAN_TIMEZONE
from .models import CalendarEvent, CalendarOccurrence


def _unfold_ics_lines(raw_ics: str) -> list[str]:
    lines = raw_ics.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    unfolded: list[str] = []
    for line in lines:
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _decode_ics_text(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def _parse_ics_params(raw_key: str) -> tuple[str, dict[str, str]]:
    parts = raw_key.split(";")
    key = parts[0].upper()
    params: dict[str, str] = {}
    for item in parts[1:]:
        if "=" not in item:
            continue
        name, raw_value = item.split("=", 1)
        params[name.upper()] = raw_value
    return key, params


def _parse_ics_dt(raw_value: str, params: dict[str, str]) -> date | datetime:
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", raw_value):
        return datetime.strptime(raw_value, "%Y%m%d").date()

    if raw_value.endswith("Z"):
        dt = datetime.strptime(raw_value, "%Y%m%dT%H%M%SZ")
        return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(GERMAN_TIMEZONE)

    tz_name = params.get("TZID")
    tzinfo = ZoneInfo(tz_name) if tz_name else GERMAN_TIMEZONE
    dt = datetime.strptime(raw_value, "%Y%m%dT%H%M%S")
    return dt.replace(tzinfo=tzinfo)


def _normalize_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=GERMAN_TIMEZONE)
    return datetime.combine(value, time.min, tzinfo=GERMAN_TIMEZONE)


def _parse_exdates(raw_values: Iterable[tuple[str, dict[str, str]]]) -> tuple[date | datetime, ...]:
    excluded: list[date | datetime] = []
    for raw_value, params in raw_values:
        for item in raw_value.split(","):
            item = item.strip()
            if item:
                excluded.append(_parse_ics_dt(item, params))
    return tuple(excluded)


def _normalize_rrule(rule: str, dtstart: datetime) -> str:
    if dtstart.tzinfo is None or "UNTIL=" not in rule:
        return rule

    normalized_parts: list[str] = []
    for part in rule.split(";"):
        if not part.startswith("UNTIL="):
            normalized_parts.append(part)
            continue

        raw_until = part.split("=", 1)[1]
        if raw_until.endswith("Z") or not re.fullmatch(r"\d{8}T\d{6}", raw_until):
            normalized_parts.append(part)
            continue

        until_dt = datetime.strptime(raw_until, "%Y%m%dT%H%M%S").replace(tzinfo=dtstart.tzinfo)
        normalized_parts.append(
            f"UNTIL={until_dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        )

    return ";".join(normalized_parts)


def parse_ics_events(raw_ics: str) -> tuple[CalendarEvent, ...]:
    unfolded = _unfold_ics_lines(raw_ics)
    current: dict[str, list[tuple[str, dict[str, str]]]] | None = None
    events: list[CalendarEvent] = []

    for line in unfolded:
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if not current:
                continue

            def first(name: str) -> tuple[str, dict[str, str]] | None:
                values = current.get(name, [])
                return values[0] if values else None

            dtstart = first("DTSTART")
            if dtstart is None:
                current = None
                continue
            dtend = first("DTEND")
            summary = first("SUMMARY")
            description = first("DESCRIPTION")
            location = first("LOCATION")
            uid = first("UID")
            recurrence = first("RRULE")

            events.append(
                CalendarEvent(
                    summary=_decode_ics_text(summary[0]) if summary else "",
                    start=_parse_ics_dt(dtstart[0], dtstart[1]),
                    end=_parse_ics_dt(dtend[0], dtend[1]) if dtend else None,
                    location=_decode_ics_text(location[0]) if location else None,
                    description=_decode_ics_text(description[0]) if description else None,
                    uid=_decode_ics_text(uid[0]) if uid else None,
                    recurrence_rule=recurrence[0] if recurrence else None,
                    excluded_starts=_parse_exdates(current.get("EXDATE", [])),
                    room_details=None,
                )
            )
            current = None
            continue

        if current is None or ":" not in line:
            continue
        raw_key, raw_value = line.split(":", 1)
        key, params = _parse_ics_params(raw_key)
        current.setdefault(key, []).append((raw_value, params))

    return tuple(events)


def _calendar_window_for_term(term_label: str) -> tuple[datetime, datetime]:
    normalized_label = term_label.casefold()
    years = [int(match) for match in re.findall(r"\d{4}", term_label)]
    if "sommer" in normalized_label and years:
        year = years[0]
        return (
            datetime(year, 4, 1, tzinfo=GERMAN_TIMEZONE),
            datetime(year, 9, 30, 23, 59, 59, tzinfo=GERMAN_TIMEZONE),
        )
    if "winter" in normalized_label and years:
        start_year = years[0]
        end_year = years[1] if len(years) > 1 else start_year + 1
        return (
            datetime(start_year, 10, 1, tzinfo=GERMAN_TIMEZONE),
            datetime(end_year, 3, 31, 23, 59, 59, tzinfo=GERMAN_TIMEZONE),
        )
    if not years:
        year = datetime.now(tz=GERMAN_TIMEZONE).year
        years = [year]
    start = datetime(min(years), 1, 1, tzinfo=GERMAN_TIMEZONE)
    end = datetime(max(years), 12, 31, 23, 59, 59, tzinfo=GERMAN_TIMEZONE)
    return start, end


def expand_ics_events(events: Iterable[CalendarEvent], term_label: str) -> tuple[CalendarOccurrence, ...]:
    window_start, window_end = _calendar_window_for_term(term_label)
    occurrences: list[CalendarOccurrence] = []

    for event in events:
        start_dt = _normalize_datetime(event.start)
        end_dt = _normalize_datetime(event.end) if event.end else None
        duration = (end_dt - start_dt) if end_dt else None
        excluded = {_normalize_datetime(item) for item in event.excluded_starts}

        if event.recurrence_rule:
            rule = rrule.rrulestr(_normalize_rrule(event.recurrence_rule, start_dt), dtstart=start_dt)
            for start in rule.between(window_start, window_end, inc=True):
                normalized_start = _normalize_datetime(start)
                if normalized_start in excluded:
                    continue
                occurrences.append(
                    CalendarOccurrence(
                        summary=event.summary,
                        start=normalized_start,
                        end=normalized_start + duration if duration else None,
                        location=event.location,
                        description=event.description,
                        room_details=event.room_details,
                        uid=event.uid,
                    )
                )
            continue

        if window_start <= start_dt <= window_end:
            occurrences.append(
                CalendarOccurrence(
                    summary=event.summary,
                    start=start_dt,
                    end=start_dt + duration if duration else end_dt,
                    location=event.location,
                    description=event.description,
                    room_details=event.room_details,
                    uid=event.uid,
                )
            )

    occurrences.sort(key=lambda item: (item.start, item.summary.casefold()))
    return tuple(occurrences)
