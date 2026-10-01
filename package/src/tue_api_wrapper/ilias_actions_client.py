from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .config import AlmaLoginError, AlmaParseError
from .ilias_actions_html import (
    build_waitlist_payload,
    find_waitlist_join_url,
    parse_course_join_result,
    parse_course_join_support,
    parse_waitlist_result,
    parse_waitlist_support,
    require_waitlist_url,
)
from .ilias_actions_models import (
    IliasActionResult,
    IliasCourseJoinResult,
    IliasCourseJoinSupport,
    IliasWaitlistResult,
    IliasWaitlistSupport,
)
from .ilias_client import IliasClient
from .ilias_registration_fields import registration_fields, validate_registration_values


def add_to_favorites(client: IliasClient, *, url: str) -> IliasActionResult:
    target = _require_ovidius_url(url)
    if "cmd=addToDesk" not in target:
        raise AlmaParseError("ILIAS favorite actions require an addToDesk URL from a search result.")
    response = client.session.get(target, timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if _looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the ILIAS favorite action redirected back to login.")
    text = " ".join(BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True).split())
    message = "Added to favorites." if "Favorit" in text or "Desktop" in text else None
    return IliasActionResult(status="submitted", message=message, final_url=response.url)


def inspect_waitlist_support(client: IliasClient, *, url: str) -> IliasWaitlistSupport:
    response = client.session.get(_require_ovidius_url(url), timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if _looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the ILIAS registration page redirected back to login.")
    return parse_waitlist_support(response.text, response.url)


def inspect_course_join_support(client: IliasClient, *, url: str) -> IliasCourseJoinSupport:
    response = _fetch_registration_page(client, url)
    return parse_course_join_support(response.text, response.url)


def join_course(
    client: IliasClient,
    *,
    url: str,
    accept_agreement: bool = False,
    registration_values: dict[str, str] | None = None,
) -> IliasCourseJoinResult:
    response = _fetch_registration_page(client, url)
    for _ in range(2):
        support = parse_course_join_support(response.text, response.url)
        join_url = find_waitlist_join_url(response.text, response.url)
        if not support.supported or join_url is None:
            raise AlmaParseError("This ILIAS page does not expose direct self-enrolment.")
        if support.requires_agreement and not accept_agreement:
            return parse_course_join_result(response.text, response.url)
        fields = registration_fields(response.text)
        if fields and registration_values is None:
            return parse_course_join_result(response.text, response.url)
        if fields:
            validate_registration_values(response.text, registration_values or {})
        payload = build_waitlist_payload(response.text, accept_agreement=accept_agreement)
        if fields:
            payload.update(registration_values or {})
        response = client.session.post(
            _require_ovidius_url(join_url), data=payload,
            timeout=client.timeout_seconds, allow_redirects=True,
        )
        response.raise_for_status()
        if _looks_logged_out(response.text):
            raise AlmaLoginError("Session is not authenticated during ILIAS course registration.")
        result = parse_course_join_result(response.text, response.url)
        if result.status not in {"requires_input", "requires_agreement"}:
            return result
    return parse_course_join_result(response.text, response.url)


def join_waitlist(
    client: IliasClient,
    *,
    url: str,
    accept_agreement: bool = False,
) -> IliasWaitlistResult:
    response = client.session.get(_require_ovidius_url(url), timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if _looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the ILIAS registration page redirected back to login.")

    join_url = find_waitlist_join_url(response.text, response.url) or response.url
    require_waitlist_url(join_url)
    response = _post_join(client, join_url, response.text, accept_agreement=False)
    result = parse_waitlist_result(response.text, response.url)
    if result.requires_agreement and not accept_agreement:
        return result
    if result.requires_agreement:
        response = _post_join(client, join_url, response.text, accept_agreement=True)
        result = parse_waitlist_result(response.text, response.url)
    return result


def _post_join(client: IliasClient, url: str, html: str, *, accept_agreement: bool):
    payload = build_waitlist_payload(html, accept_agreement=accept_agreement)
    response = client.session.post(
        url,
        data=payload,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if _looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the ILIAS waitlist action redirected back to login.")
    return response


def _fetch_registration_page(client: IliasClient, url: str):
    response = client.session.get(_require_ovidius_url(url), timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if _looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the ILIAS registration page redirected back to login.")
    return response


def _require_ovidius_url(url: str) -> str:
    value = url.strip()
    if not value:
        raise AlmaParseError("A non-empty ILIAS URL is required.")
    if not value.startswith(("http://", "https://")):
        value = urljoin("https://ovidius.uni-tuebingen.de/", value.lstrip("/"))
    host = urlparse(value).netloc
    if host != "ovidius.uni-tuebingen.de":
        raise AlmaParseError("ILIAS action URLs must belong to ovidius.uni-tuebingen.de.")
    return value


def _looks_logged_out(html: str) -> bool:
    return "cmd=force_login" in html or "Shibboleth" in html and "j_username" in html
