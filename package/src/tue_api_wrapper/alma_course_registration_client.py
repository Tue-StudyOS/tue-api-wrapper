from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from .alma_course_registration_html import (
    build_registration_confirm_request,
    extract_registration_messages,
    extract_registration_options,
    extract_registration_start_request,
    extract_registration_status,
    _safe_detail_identity,
)
from .alma_course_registration_models import (
    AlmaCourseRegistrationOptions,
    AlmaCourseRegistrationResult,
    AlmaCourseRegistrationSupport,
)
from .config import AlmaLoginError, AlmaParseError

if TYPE_CHECKING:
    import requests

    from .client import AlmaClient
    from .alma_course_registration_html import AlmaRegistrationStartRequest


def inspect_course_registration_support(client: "AlmaClient", detail_url: str) -> AlmaCourseRegistrationSupport:
    detail_url = _normalize_detail_url(client, detail_url)
    response = _get_authenticated_html(client, detail_url)
    start = extract_registration_start_request(response.text, response.url)
    messages = extract_registration_messages(response.text)
    status = extract_registration_status(response.text, messages)
    if start is None:
        title, number = _safe_detail_identity(response.text, response.url)
        return AlmaCourseRegistrationSupport(
            detail_url=response.url,
            title=title,
            number=number,
            supported=False,
            action=None,
            status=status,
            messages=messages,
            message="This Alma detail page does not expose a course-registration action.",
        )
    return AlmaCourseRegistrationSupport(
        detail_url=response.url,
        title=start.title,
        number=start.number,
        supported=True,
        action=start.action,
        status=status,
        messages=messages,
    )


def prepare_course_registration(client: "AlmaClient", detail_url: str) -> AlmaCourseRegistrationOptions:
    detail_url = _normalize_detail_url(client, detail_url)
    response = _get_authenticated_html(client, detail_url)
    start = extract_registration_start_request(response.text, response.url)
    if start is None:
        raise AlmaParseError("This Alma detail page does not expose a course-registration action.")

    confirm = _post_start_request(client, start)
    options = extract_registration_options(confirm.text)
    messages = extract_registration_messages(confirm.text)
    if not options:
        raise AlmaParseError("Alma did not expose a selectable course-registration path after opening registration.")

    return AlmaCourseRegistrationOptions(
        detail_url=response.url,
        title=start.title,
        number=start.number,
        action=start.action,
        options=options,
        messages=messages,
    )


def register_for_course(
    client: "AlmaClient",
    detail_url: str,
    *,
    planelement_id: str | None = None,
    expected_option_label: str | None = None,
    expected_title: str | None = None,
    expected_number: str | None = None,
    expected_action_name: str | None = None,
) -> AlmaCourseRegistrationResult:
    detail_url = _normalize_detail_url(client, detail_url)
    response = _get_authenticated_html(client, detail_url)
    start = extract_registration_start_request(response.text, response.url)
    if start is None:
        raise AlmaParseError("This Alma detail page does not expose a course-registration action.")

    confirm = _post_start_request(client, start)
    request = build_registration_confirm_request(
        confirm.text,
        confirm.url,
        planelement_id=planelement_id,
    )
    if expected_option_label is not None and (request.selected_option.label != expected_option_label or start.title != expected_title or start.number != expected_number or start.action != "ANMELDUNG" or request.selected_option.action_name != expected_action_name):
        raise AlmaParseError("The reviewed registration target or option changed; inspect it again.")
    final = client.session.post(
        request.action_url,
        data=request.payload,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    final.raise_for_status()
    if client._looks_logged_out(final.text):
        raise AlmaLoginError("Session is not authenticated; the Alma registration action redirected back to login.")

    messages = extract_registration_messages(final.text)
    return AlmaCourseRegistrationResult(
        detail_url=response.url,
        final_url=final.url,
        title=start.title,
        number=start.number,
        action=start.action,
        selected_option=request.selected_option,
        messages=messages,
        status=extract_registration_status(final.text, messages),
    )


def _normalize_detail_url(client: "AlmaClient", detail_url: str) -> str:
    normalized = detail_url.strip()
    if not normalized:
        raise AlmaParseError("A non-empty Alma detail URL is required.")
    if not urlparse(normalized).scheme:
        normalized = urljoin(f"{client.base_url}/", normalized)
    parsed = urlparse(normalized)
    base = urlparse(client.base_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc or not parsed.path.startswith("/alma/"):
        raise AlmaParseError("Alma course-registration URLs must belong to the configured Alma host.")
    return normalized


def _get_authenticated_html(client: "AlmaClient", url: str) -> "requests.Response":
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma detail page redirected back to login.")
    return response


def _post_start_request(
    client: "AlmaClient",
    start: "AlmaRegistrationStartRequest",
) -> "requests.Response":
    kwargs: dict[str, object]
    if start.enctype and "multipart/form-data" in start.enctype.casefold():
        kwargs = {"files": {name: (None, value) for name, value in start.payload.items()}}
    else:
        kwargs = {"data": start.payload}

    response = client.session.post(
        start.action_url,
        timeout=client.timeout_seconds,
        allow_redirects=True,
        **kwargs,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma registration flow redirected back to login.")
    return response
