from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from .alma_availability import raise_for_alma_unavailable_page
from .alma_timetable_html import parse_timetable_contract
from .config import AlmaParseError
from .models import LoginForm


def extract_login_form(html: str, page_url: str) -> LoginForm:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="loginForm") or soup.find("form", id="mobileLoginForm")
    if form is None:
        raise_for_alma_unavailable_page(html)
        raise AlmaParseError("Could not find Alma login form.")

    payload: dict[str, str] = {}
    for field in form.find_all("input"):
        name = field.get("name")
        field_type = field.get("type", "")
        if not name or field_type in {"checkbox", "button"}:
            continue
        payload[name] = field.get("value", "")

    payload.setdefault("submit", "")
    return LoginForm(action_url=urljoin(page_url, form["action"]), payload=payload)


def extract_timetable_terms(html: str) -> dict[str, str]:
    contract = parse_timetable_contract(html, "")
    if not contract.terms:
        raise AlmaParseError("Could not find the timetable term selector.")

    return {option.label: option.value for option in contract.terms}


def extract_timetable_export_url(html: str) -> str:
    contract = parse_timetable_contract(html, "")
    if contract.export_url is None:
        raise AlmaParseError("Could not find the timetable iCalendar export field.")

    return contract.export_url


def build_term_export_url(export_url: str, term_id: str) -> str:
    parsed = urlparse(export_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["termgroup"] = term_id
    return urlunparse(parsed._replace(query=urlencode(query)))
