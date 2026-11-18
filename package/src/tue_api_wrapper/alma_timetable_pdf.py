from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
import textwrap

from .alma_timetable_client import fetch_timetable_view
from .client import AlmaClient
from .models import CalendarOccurrence
from .simple_pdf import SimplePdf


@dataclass(frozen=True)
class RenderedPdf:
    filename: str
    content_type: str
    data: bytes


def render_timetable_pdf(
    client: AlmaClient,
    *,
    term: str | None = None,
    week: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    single_day: str | None = None,
) -> RenderedPdf:
    view = fetch_timetable_view(
        client,
        term=term,
        week=week,
        from_date=from_date,
        to_date=to_date,
        single_day=single_day,
        limit=2000,
    )
    title = f"Alma timetable - {view.selected_term_label or 'selected term'}"
    subtitle = _range_label(view.visible_range_start, view.visible_range_end)
    pdf = SimplePdf()
    cursor = _draw_header(pdf, title, subtitle)

    occurrences = sorted((item for item in view.occurrences if item.status != "cancelled"), key=lambda item: item.start)
    current_day: date | None = None
    if not occurrences:
        pdf.text(42, cursor, "No timetable events found for this selection.", size=11, color=(0.15, 0.15, 0.15))
    for item in occurrences:
        if current_day != item.start.date():
            current_day = item.start.date()
            cursor = _ensure_space(pdf, cursor, 42)
            cursor = _draw_day_header(pdf, cursor, current_day)
        cursor = _ensure_space(pdf, cursor, _event_height(item))
        cursor = _draw_event(pdf, cursor, item)

    return RenderedPdf(
        filename=_filename(view.selected_term_label, view.visible_range_start, view.visible_range_end),
        content_type="application/pdf",
        data=pdf.render(),
    )


def _draw_header(pdf: SimplePdf, title: str, subtitle: str) -> float:
    pdf.rect(0, 0, pdf.width, pdf.height, fill=(0.98, 0.98, 0.96))
    pdf.rect(0, pdf.height - 96, pdf.width, 96, fill=(0.07, 0.17, 0.16))
    pdf.text(42, pdf.height - 48, title, size=20, color=(1, 1, 1))
    pdf.text(42, pdf.height - 72, subtitle, size=10.5, color=(0.82, 0.9, 0.86))
    return pdf.height - 128


def _draw_day_header(pdf: SimplePdf, cursor: float, day: date) -> float:
    pdf.rect(42, cursor - 18, pdf.width - 84, 24, fill=(0.86, 0.91, 0.88))
    pdf.text(54, cursor - 10, day.strftime("%A, %d.%m.%Y"), size=11.5, color=(0.06, 0.18, 0.14))
    return cursor - 34


def _draw_event(pdf: SimplePdf, cursor: float, item: CalendarOccurrence) -> float:
    height = _event_height(item)
    left = 42
    width = pdf.width - 84
    pdf.rect(left, cursor - height + 8, width, height, fill=(1, 1, 1))
    pdf.line(left, cursor + 8, left + width, cursor + 8, color=(0.73, 0.78, 0.75), width=0.7)
    pdf.text(left + 12, cursor - 10, _time_label(item), size=10.5, color=(0.08, 0.24, 0.2))

    text_x = left + 92
    y = cursor - 10
    for line in _wrap(item.summary, 54)[:3]:
        pdf.text(text_x, y, line, size=10.5, color=(0.08, 0.08, 0.07))
        y -= 14
    if item.location:
        for line in _wrap(f"Room: {item.location}", 60)[:2]:
            pdf.text(text_x, y, line, size=8.8, color=(0.3, 0.33, 0.31))
            y -= 12
    if item.description:
        for line in _wrap(_clean_description(item.description), 68)[:2]:
            pdf.text(text_x, y, line, size=8.5, color=(0.36, 0.36, 0.34))
            y -= 11
    return cursor - height - 10


def _ensure_space(pdf: SimplePdf, cursor: float, needed: float) -> float:
    if cursor - needed >= 52:
        return cursor
    pdf.add_page()
    return _draw_header(pdf, "Alma timetable", "continued")


def _event_height(item: CalendarOccurrence) -> float:
    lines = len(_wrap(item.summary, 54)[:3])
    if item.location:
        lines += len(_wrap(f"Room: {item.location}", 60)[:2])
    if item.description:
        lines += len(_wrap(_clean_description(item.description), 68)[:2])
    return max(48, 22 + (lines * 13))


def _time_label(item: CalendarOccurrence) -> str:
    start = item.start.strftime("%H:%M")
    if item.end is None:
        return start
    return f"{start}-{item.end.strftime('%H:%M')}"


def _wrap(value: str, width: int) -> list[str]:
    return textwrap.wrap(" ".join(value.split()), width=width, break_long_words=False) or [""]


def _clean_description(value: str) -> str:
    return re.sub(r"https?://\\S+", "", " ".join(value.split())).strip()


def _range_label(start: date | None, end: date | None) -> str:
    if start is None or end is None:
        return "All visible events"
    if start == end:
        return start.strftime("%d.%m.%Y")
    return f"{start.strftime('%d.%m.%Y')} to {end.strftime('%d.%m.%Y')}"


def _filename(term: str | None, start: date | None, end: date | None) -> str:
    base = "alma-timetable"
    if term:
        base += "-" + re.sub(r"[^A-Za-z0-9]+", "-", term).strip("-").lower()
    if start is not None:
        base += "-" + start.isoformat()
    if end is not None and end != start:
        base += "-" + end.isoformat()
    return f"{base}.pdf"
