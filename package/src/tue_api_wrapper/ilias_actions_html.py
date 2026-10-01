from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .ilias_registration_fields import registration_fields
from .ilias_actions_models import (
    IliasCourseJoinResult,
    IliasCourseJoinSupport,
    IliasWaitlistResult,
    IliasWaitlistSupport,
)


def find_waitlist_join_url(html: str, page_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", action=lambda value: bool(value and "ilCourseRegistrationGUI" in value))
    if form is not None:
        return urljoin(page_url, form.get("action", page_url))
    if "ilCourseRegistrationGUI" in page_url:
        return page_url
    link = soup.find("a", href=lambda value: bool(value and "ilCourseRegistrationGUI" in value))
    return urljoin(page_url, link["href"]) if link else None


def parse_course_join_support(html: str, page_url: str) -> IliasCourseJoinSupport:
    join_url = find_waitlist_join_url(html, page_url)
    text = _page_text(html)
    join_label = _join_control_label(html)
    direct_join = join_label is not None and "Warteliste" not in f"{text} {join_label}"
    return IliasCourseJoinSupport(
        supported=direct_join,
        requires_agreement=_requires_agreement(html),
        join_url=_sanitized_registration_url(join_url) if direct_join and join_url else None,
        message="Direct self-enrolment is available." if direct_join else None,
        registration_fields=registration_fields(html),
    )


def parse_course_join_result(html: str, final_url: str) -> IliasCourseJoinResult:
    text = _page_text(html)
    requires_agreement = _requires_agreement(html)
    if registration_fields(html):
        status = "requires_input"
    elif requires_agreement:
        status = "requires_agreement"
    elif "Sie sind dem Kurs beigetreten" in text or re.search(r"Status der Mitgliedschaft:\s*Kursmitglied", text):
        status = "joined"
    else:
        status = "submitted"
    return IliasCourseJoinResult(
        status=status,
        message=_first_direct_join_message(text),
        final_url=_sanitized_registration_url(final_url),
        requires_agreement=requires_agreement,
        registration_fields=registration_fields(html),
    )


def build_waitlist_payload(html: str, *, accept_agreement: bool = False) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    payload: dict[str, str] = {}
    form = soup.find("form", action=lambda value: bool(value and "ilCourseRegistrationGUI" in value))
    if form is not None:
        for field in form.find_all(["input", "button"]):
            name = field.get("name")
            if not name:
                continue
            field_type = field.get("type", "").lower()
            if field_type in {"button", "file", "image", "password", "reset"}:
                continue
            if field_type in {"checkbox", "radio"} and not field.has_attr("checked"):
                continue
            if name == "agreement" and not accept_agreement:
                continue
            payload[name] = field.get("value") or field.get_text(" ", strip=True)

    join_name = next((name for name in payload if name in {"cmd[join]", "cmd%5Bjoin%5D"}), None)
    if join_name is None:
        payload["cmd[join]"] = "In Warteliste eintragen"
    if accept_agreement:
        payload["agreement"] = "1"
    return payload


def parse_waitlist_support(html: str, page_url: str) -> IliasWaitlistSupport:
    join_url = find_waitlist_join_url(html, page_url)
    text = _page_text(html)
    supported = "Warteliste" in f"{text} {_join_control_label(html) or ''}"
    return IliasWaitlistSupport(
        supported=supported,
        requires_agreement=_requires_agreement(html),
        join_url=_sanitized_registration_url(join_url) if join_url else None,
        message=_first_relevant_message(text),
    )


def parse_waitlist_result(html: str, final_url: str) -> IliasWaitlistResult:
    text = _page_text(html)
    position = _waitlist_position(text)
    requires_agreement = _requires_agreement(html)
    if requires_agreement:
        status = "requires_agreement"
    elif position is not None or "Warteliste aufgenommen" in text or "Eingetragen auf der Warteliste" in text:
        status = "joined_waitlist"
    elif "bereits" in text and ("Mitglied" in text or "Warteliste" in text):
        status = "already_registered"
    else:
        status = "submitted"
    return IliasWaitlistResult(
        status=status,
        message=_first_relevant_message(text),
        final_url=final_url,
        waitlist_position=position,
        requires_agreement=requires_agreement,
    )


def require_waitlist_url(url: str) -> None:
    if "ilCourseRegistrationGUI" not in url:
        raise AlmaParseError("The ILIAS URL does not expose the course-registration GUI.")


def _requires_agreement(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    agreement = soup.find(attrs={"name": "agreement"})
    if agreement is not None:
        return True
    text = _page_text(html)
    return "Nutzungsvereinbarung" in text and "Einverständnis" not in text


def _join_control_label(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    control = soup.find(attrs={"name": "cmd[join]"})
    if control is None:
        return None
    return str(control.get("value") or control.get_text(" ", strip=True))


def _first_direct_join_message(text: str) -> str | None:
    for pattern in (
        r"Sie sind dem Kurs beigetreten\.",
        r"Status der Mitgliedschaft:\s*[^.]+",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _page_text(html: str) -> str:
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ", strip=True).split())


def _waitlist_position(text: str) -> int | None:
    match = re.search(r"Platz\s+(\d+)\s+auf\s+der\s+Warteliste", text)
    return int(match.group(1)) if match else None


def _first_relevant_message(text: str) -> str | None:
    for pattern in (
        r"Sie sind in die Warteliste aufgenommen worden\.",
        r"Sie haben Platz \d+ auf der Warteliste\.",
        r"Status der Mitgliedschaft:\s*[^.]+",
        r"Zu dieser Nutzungsvereinbarung haben Sie ihr Einverständnis erklärt\.",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _sanitized_registration_url(url: str) -> str:
    parsed = urlsplit(url)
    query = urlencode([(key, value) for key, value in parse_qsl(parsed.query) if key != "rtoken"])
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
