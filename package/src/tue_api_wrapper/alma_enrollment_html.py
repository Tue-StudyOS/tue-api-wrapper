from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .alma_enrollment_models import AlmaEnrollmentEntry
from .config import AlmaParseError
from .models import AlmaEnrollmentPage


TERM_FIELD = "studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input"
HEADING_RE = re.compile(r"^(?P<category>Veranstaltung|Prüfung):\s*(?P<title>.+)$")
CODE_RE = re.compile(r"^(?P<number>[A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*\d+[A-Z]*|GTCNEURO)\s+(?P<title>.+)$")
EMBEDDED_CODE_RE = re.compile(r"(?P<number>[A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*\d+[A-Z]*|GTCNEURO)\s+(?P<title>.+)$")
SCHEDULE_NOISE_RE = re.compile(
    r"\b(?:Status|Aktionen|Details anzeigen|Informationen zu Belegzeiträumen|"
    r"Ab-/Ummelden|Raumdetails für .+? anzeigen)\b"
)


def parse_enrollment_page(html: str, page_url: str = "https://alma.uni-tuebingen.de") -> AlmaEnrollmentPage:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="studentOverviewForm")
    if form is None:
        raise AlmaParseError("Could not find the Alma enrollment overview form.")

    select = form.find("select", attrs={"name": TERM_FIELD})
    if select is None:
        raise AlmaParseError("Could not find the Alma enrollment term selector.")

    terms, selected_term = _term_options(select)
    return AlmaEnrollmentPage(
        selected_term=selected_term,
        available_terms=terms,
        message=_page_message(form),
        entries=_enrollment_entries(form, page_url),
    )


def _term_options(select) -> tuple[dict[str, str], str | None]:
    terms: dict[str, str] = {}
    selected_term: str | None = None
    for option in select.find_all("option"):
        label = _clean(option.get_text(" ", strip=True))
        value = option.get("value", "").strip()
        if label and value:
            terms[label] = value
            if option.has_attr("selected"):
                selected_term = label
    return terms, selected_term


def _page_message(form) -> str | None:
    text = _clean(form.get_text(" ", strip=True))
    match = re.search(r"Sie haben bisher.+?(?:angemeldet\.|zugelassen\.)", text)
    return match.group(0) if match else None


def _enrollment_entries(form, page_url: str) -> tuple[AlmaEnrollmentEntry, ...]:
    entries: list[AlmaEnrollmentEntry] = []
    for heading in form.find_all("h2"):
        match = HEADING_RE.match(_clean(heading.get_text(" ", strip=True)))
        if match is None:
            continue
        category = match.group("category")
        table = heading.find_next("table")
        if table is None:
            continue
        schedule_text = _schedule_text(table)
        event_type, number, title = _entry_identity(category, match.group("title"), schedule_text)
        status_text = _status_text(table)
        entries.append(
            AlmaEnrollmentEntry(
                category=category,
                title=title,
                number=number,
                event_type=event_type,
                status=_extract_after_label(status_text, "Ihr aktueller Status"),
                semester=_extract_after_label(status_text, "Semester der Leistung"),
                schedule_text=schedule_text,
                detail_url=_detail_url(table, page_url),
                attempt=_extract_after_label(status_text, "Versuch (gilt nur für Prüfungen)"),
            )
        )
    return tuple(entries)


def _split_code(value: str) -> tuple[str | None, str]:
    match = CODE_RE.match(_clean(value))
    if match is None:
        return None, _clean(value)
    return match.group("number"), match.group("title")


def _entry_identity(category: str, heading_title: str, schedule_text: str | None) -> tuple[str | None, str | None, str]:
    if category == "Prüfung":
        number, fallback_title = _split_code(heading_title)
        return category, number, _exam_title(schedule_text) or fallback_title

    match = EMBEDDED_CODE_RE.search(_clean(heading_title))
    if match is None:
        return category, *_split_code(heading_title)
    event_type = _clean(heading_title[: match.start()])
    return event_type or category, match.group("number"), match.group("title")


def _exam_title(schedule_text: str | None) -> str | None:
    if not schedule_text:
        return None
    value = re.sub(r"^\d+\.\s*Parallelgruppe\s+", "", schedule_text).strip()
    value = re.split(
        r"\s+(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+\d{2}\.\d{2}\.\d{2}\b",
        value,
        maxsplit=1,
    )[0]
    value = re.split(r"\s+(?:Keine Uhrzeit festgelegt|Prüfungsform:|Prüfer/-in:)", value, maxsplit=1)[0]
    return _clean(value) or None


def _extract_after_label(text: str, label: str) -> str | None:
    match = re.search(fr"{re.escape(label)}:\s*([^:]+?)(?=\s+[A-ZÄÖÜ][^:]+:|$)", text)
    return _clean(match.group(1)) if match else None


def _schedule_text(table) -> str | None:
    candidates = [_clean(cell.get_text(" ", strip=True)) for cell in table.find_all("td")]
    if not candidates:
        return None
    value = next(
        (
            candidate
            for candidate in candidates
            if "Ihr aktueller Status:" not in candidate
            and (
                "Parallelgruppe" in candidate
                or "Prüfungsform:" in candidate
                or re.search(r"\b\d{2}\.\d{2}\.\d{2}\b", candidate)
            )
        ),
        candidates[0],
    )
    value = _clean(SCHEDULE_NOISE_RE.sub(" ", value))
    return value or None


def _status_text(table) -> str:
    for cell in table.find_all("td"):
        value = _clean(cell.get_text(" ", strip=True))
        if "Ihr aktueller Status:" in value:
            return value
    return _clean(table.get_text(" ", strip=True))


def _detail_url(table, page_url: str) -> str | None:
    link = table.find("a", href=lambda value: bool(value and "_flowId=detailView-flow" in value))
    return urljoin(page_url, link["href"]) if link is not None else None


def _clean(value: str) -> str:
    return " ".join(value.split())
