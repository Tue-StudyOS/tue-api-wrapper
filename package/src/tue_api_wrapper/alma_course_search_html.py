from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .alma_course_search_models import (
    AlmaCourseSearchForm,
    AlmaCourseSearchPage,
    AlmaCourseSearchResult,
    AlmaCourseSearchTermOption,
)
from .config import AlmaParseError


COURSE_SEARCH_URL = (
    "https://alma.uni-tuebingen.de/alma/pages/startFlow.xhtml"
    "?_flowId=searchCourseNonStaff-flow"
    "&navigationPosition=studiesOffered,searchCourseNonStaff"
    "&recordRequest=true"
)


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _parse_course_search_results(html: str, page_url: str) -> tuple[AlmaCourseSearchResult, ...]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[AlmaCourseSearchResult] = []
    table = soup.find("table", attrs={"id": lambda value: bool(value and "genSearchRes" in value and value.endswith("Table"))})
    if table is None:
        return ()

    for row in table.find_all("tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 8:
            continue
        detail_link = next((link.get("href") for link in cells[0].find_all("a", href=True)), None)
        title = _clean_text(cells[2].get_text(" ", strip=True))
        if not title:
            continue
        results.append(
            AlmaCourseSearchResult(
                number=_clean_text(cells[1].get_text(" ", strip=True)) or None,
                title=title,
                event_type=_clean_text(cells[3].get_text(" ", strip=True)) or None,
                responsible_lecturer=_clean_text(cells[4].get_text(" ", strip=True)) or None,
                lecturer=_clean_text(cells[5].get_text(" ", strip=True)) or None,
                organization=_clean_text(cells[6].get_text(" ", strip=True)) or None,
                detail_url=urljoin(page_url, detail_link) if detail_link else None,
            )
        )
    return tuple(results)


def extract_course_search_form(html: str, page_url: str) -> AlmaCourseSearchForm:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="genericSearchMask")
    if form is None:
        raise AlmaParseError("Could not find the Alma course-search form.")

    payload: dict[str, str] = {}
    for field in form.find_all(["input", "select"]):
        name = field.get("name")
        if not name:
            continue
        if field.name == "select":
            selected = field.find("option", selected=True)
            payload[name] = selected.get("value", "") if selected is not None else ""
            continue

        field_type = field.get("type", "")
        if field_type in {"button", "file", "image", "password", "radio", "reset", "submit"}:
            continue
        if field_type == "checkbox":
            if field.has_attr("checked"):
                payload[name] = field.get("value", "true")
            continue
        payload[name] = field.get("value", "")

    query_field = form.find(
        "input",
        attrs={
            "type": "text",
            "placeholder": lambda value: bool(value and "Dozent" in value),
            "name": lambda value: bool(value and ":termSelect_" not in value and not value.endswith("_focus")),
        },
    )
    if query_field is None or not query_field.get("name"):
        raise AlmaParseError("Could not identify the Alma course-search query field.")

    term_select = form.find("select", attrs={"name": lambda value: bool(value and value.endswith(":termSelect_input"))})
    if term_select is None or not term_select.get("name"):
        raise AlmaParseError("Could not identify the Alma course-search term field.")

    search_button = form.find("button", attrs={"name": lambda value: bool(value and value.endswith(":search"))})
    if search_button is None or not search_button.get("name"):
        raise AlmaParseError("Could not identify the Alma course-search submit button.")

    term_options = tuple(
        AlmaCourseSearchTermOption(
            value=option.get("value", ""),
            label=option.get("data-title", "") or _clean_text(option.get_text(" ", strip=True)),
            is_selected=option.has_attr("selected"),
        )
        for option in term_select.find_all("option")
        if option.get("value", "").strip()
    )

    return AlmaCourseSearchForm(
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
        query_field_name=query_field["name"],
        term_field_name=term_select["name"],
        search_button_name=search_button["name"],
        term_options=term_options,
    )


def validate_course_search_response(html: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    if soup.select_one(".ui-messages-error, .ui-message-error, .alert-danger") is not None or "Keine gültige Auswahl" in text:
        raise AlmaParseError("Alma rejected the course-search form; check the search criteria and semester.")
    table = soup.find("table", id=lambda value: bool(value and "genSearchRes" in value and value.endswith("Table")))
    empty = any(marker in text for marker in ("Keine Veranstaltungen gefunden", "Keine Ergebnisse gefunden"))
    if soup.find("form", id="genericSearchMask") is None and table is None and not empty:
        raise AlmaParseError("The response did not look like an Alma course-search page.")


def parse_course_search_page(html: str, page_url: str, *, query: str) -> AlmaCourseSearchPage:
    validate_course_search_response(html)
    form = extract_course_search_form(html, page_url)
    results = _parse_course_search_results(html, page_url)
    selected_term = next((option for option in form.term_options if option.is_selected), None)
    if not results and "Veranstaltungen suchen" not in html:
        raise AlmaParseError("The response did not look like an Alma course-search page.")

    return AlmaCourseSearchPage(
        page_url=page_url,
        query=query,
        selected_term_value=selected_term.value if selected_term is not None else None,
        selected_term_label=selected_term.label if selected_term is not None else None,
        term_options=form.term_options,
        results=results,
    )
