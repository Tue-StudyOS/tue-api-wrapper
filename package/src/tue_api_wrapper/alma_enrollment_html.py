from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .alma_enrollment_models import AlmaEnrollmentEntry
from .config import AlmaParseError
from .models import AlmaEnrollmentPage


TERM_FIELD = "studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input"
HEADING_RE = re.compile(r"^Veranstaltung:\s*(?P<type>.+?)\s+(?P<title>.+)$")
CODE_RE = re.compile(r"^(?P<number>[A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*\d+[A-Z]?|GTCNEURO)\s+(?P<title>.+)$")
SCHEDULE_NOISE_RE = re.compile(
    r"\b(?:Status|Aktionen|Details anzeigen|Informationen zu Belegzeiträumen|"
    r"Raumdetails für .+? anzeigen)\b"
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
        event_type = match.group("type")
        number, title = _split_code(match.group("title"))
        table = heading.find_next("table")
        if table is None:
            continue
        status_text = _status_text(table)
        entries.append(
            AlmaEnrollmentEntry(
                title=title,
                number=number,
                event_type=event_type,
                status=_extract_after_label(status_text, "Ihr aktueller Status"),
                semester=_extract_after_label(status_text, "Semester der Leistung"),
                schedule_text=_schedule_text(table),
                detail_url=_detail_url(table, page_url),
            )
        )
    return tuple(entries)


def _split_code(value: str) -> tuple[str | None, str]:
    match = CODE_RE.match(_clean(value))
    if match is None:
        return None, _clean(value)
    return match.group("number"), match.group("title")


def _extract_after_label(text: str, label: str) -> str | None:
    match = re.search(fr"{re.escape(label)}:\s*([^:]+?)(?=\s+[A-ZÄÖÜ][^:]+:|$)", text)
    return _clean(match.group(1)) if match else None


def _schedule_text(table) -> str | None:
    cells = table.find_all("td")
    if not cells:
        return None
    value = _clean(cells[0].get_text(" ", strip=True))
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
