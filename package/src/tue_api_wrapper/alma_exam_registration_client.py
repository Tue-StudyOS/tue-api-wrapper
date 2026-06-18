from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from .alma_exam_registration_helpers import control_identity, find_detail_form
from .alma_exam_registration_html import (
    AlmaExamDetailOpenRequest,
    build_exam_detail_open_request,
    build_exam_registration_confirm_request,
    build_instruction_accept_request,
    extract_exam_registration_messages,
    extract_exam_registration_options,
    extract_exam_registration_start_request,
    extract_exam_registration_status,
)
from .alma_exam_registration_models import (
    AlmaExamRegistrationOptions,
    AlmaExamRegistrationResult,
    AlmaExamRegistrationSupport,
)
from .config import AlmaLoginError, AlmaParseError
from .html_forms import extract_form_payload

if TYPE_CHECKING:
    import requests

    from .client import AlmaClient


@dataclass(frozen=True)
class _ExamPage:
    html: str
    url: str
    source_url: str
    exam_unit_id: str | None


def inspect_exam_registration_support(
    client: "AlmaClient",
    source_url: str | None = None,
    *,
    exam_unit_id: str | None = None,
) -> AlmaExamRegistrationSupport:
    try:
        page = _resolve_exam_page(client, source_url, exam_unit_id=exam_unit_id)
        start = extract_exam_registration_start_request(page.html, page.url)
    except AlmaParseError as error:
        return AlmaExamRegistrationSupport(
            source_url=(source_url or client.timetable_url).strip() or client.timetable_url,
            title=None,
            number=None,
            exam_unit_id=exam_unit_id,
            supported=False,
            action=None,
            message=str(error),
        )

    if start is None:
        messages = extract_exam_registration_messages(page.html)
        return AlmaExamRegistrationSupport(
            source_url=page.source_url,
            title=None,
            number=None,
            exam_unit_id=page.exam_unit_id,
            supported=False,
            action=None,
            status=extract_exam_registration_status(page.html, messages),
            messages=messages,
            message="This Alma page does not expose an exam-registration action.",
        )

    messages = extract_exam_registration_messages(page.html)
    return AlmaExamRegistrationSupport(
        source_url=page.source_url,
        title=start.title,
        number=start.number,
        exam_unit_id=start.exam_unit_id or page.exam_unit_id,
        supported=True,
        action=start.action,
        status=extract_exam_registration_status(page.html, messages),
        messages=messages,
    )


def prepare_exam_registration(
    client: "AlmaClient",
    source_url: str | None = None,
    *,
    exam_unit_id: str | None = None,
) -> AlmaExamRegistrationOptions:
    page = _resolve_exam_page(client, source_url, exam_unit_id=exam_unit_id)
    start = extract_exam_registration_start_request(page.html, page.url)
    if start is None:
        raise AlmaParseError("This Alma page does not expose an exam-registration action.")

    stage, accepted_instruction = _open_exam_registration(client, start)
    options = extract_exam_registration_options(stage.text)
    if not options:
        raise AlmaParseError("Alma did not expose a selectable exam-registration path after opening registration.")

    return AlmaExamRegistrationOptions(
        source_url=page.source_url,
        title=start.title,
        number=start.number,
        exam_unit_id=start.exam_unit_id or page.exam_unit_id,
        action=start.action,
        options=options,
        messages=extract_exam_registration_messages(stage.text),
        requires_instruction_accept=accepted_instruction,
    )


def register_for_exam(
    client: "AlmaClient",
    source_url: str | None = None,
    *,
    exam_unit_id: str | None = None,
    planelement_id: str | None = None,
) -> AlmaExamRegistrationResult:
    page = _resolve_exam_page(client, source_url, exam_unit_id=exam_unit_id)
    start = extract_exam_registration_start_request(page.html, page.url)
    if start is None:
        raise AlmaParseError("This Alma page does not expose an exam-registration action.")

    stage, _ = _open_exam_registration(client, start)
    request = build_exam_registration_confirm_request(stage.text, stage.url, planelement_id=planelement_id)
    final = client.session.post(
        request.action_url,
        data=request.payload,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    final.raise_for_status()
    if client._looks_logged_out(final.text):
        raise AlmaLoginError("Session is not authenticated; the Alma exam-registration action redirected back to login.")

    messages = extract_exam_registration_messages(final.text)
    return AlmaExamRegistrationResult(
        source_url=page.source_url,
        final_url=final.url,
        title=start.title,
        number=start.number,
        exam_unit_id=start.exam_unit_id or page.exam_unit_id,
        action=start.action,
        selected_option=request.selected_option,
        messages=messages,
        status=extract_exam_registration_status(final.text, messages),
    )


def _resolve_exam_page(client: "AlmaClient", source_url: str | None, *, exam_unit_id: str | None) -> _ExamPage:
    response = _get_authenticated_html(client, _normalize_source_url(client, source_url))
    start = extract_exam_registration_start_request(response.text, response.url)
    if start is not None:
        return _ExamPage(response.text, response.url, response.url, start.exam_unit_id)

    html = response.text
    page_url = response.url
    try:
        open_request = build_exam_detail_open_request(html, page_url, exam_unit_id=exam_unit_id)
    except AlmaParseError:
        tab_response = _open_linked_exams_tab(client, html, page_url)
        html = tab_response.text
        page_url = tab_response.url
        open_request = build_exam_detail_open_request(html, page_url, exam_unit_id=exam_unit_id)

    detail = _post_form_request(client, open_request)
    if extract_exam_registration_start_request(detail.text, detail.url) is None:
        raise AlmaParseError("Opening the linked Alma exam did not expose an exam-registration action.")
    return _ExamPage(detail.text, detail.url, response.url, open_request.exam_unit_id)


def _open_exam_registration(client: "AlmaClient", start) -> tuple["requests.Response", bool]:
    stage = _post_form_request(client, start)
    accept = build_instruction_accept_request(stage.text, stage.url)
    if accept is None:
        return stage, False
    return _post_form_request(client, accept), True


def _open_linked_exams_tab(client: "AlmaClient", html: str, page_url: str) -> "requests.Response":
    soup = BeautifulSoup(html, "html.parser")
    form = find_detail_form(soup)
    if not isinstance(form, Tag):
        raise AlmaParseError("Alma did not expose the detail form for linked exams.")

    trigger = next(
        (control for control in form.find_all(["button", "input", "a"]) if "linkedexaminationstab" in control_identity(control)),
        None,
    )
    if trigger is None:
        raise AlmaParseError("Alma did not expose a linked examinations tab.")

    form_id = form.get("id") or form.get("name") or "detailViewData"
    target = trigger.get("name") or trigger.get("id")
    if not target:
        raise AlmaParseError("Alma did not expose a linked examinations tab action.")
    payload = extract_form_payload(form)
    payload.setdefault(f"{form_id}_SUBMIT", "1")
    payload[f"{form_id}:_idcl"] = target
    request = AlmaExamDetailOpenRequest(
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
        enctype=form.get("enctype"),
        exam_unit_id="",
    )
    return _post_form_request(client, request)


def _post_form_request(client: "AlmaClient", request) -> "requests.Response":
    kwargs: dict[str, object]
    if getattr(request, "enctype", None) and "multipart/form-data" in request.enctype.casefold():
        kwargs = {"files": {name: (None, value) for name, value in request.payload.items()}}
    else:
        kwargs = {"data": request.payload}
    response = client.session.post(
        request.action_url,
        timeout=client.timeout_seconds,
        allow_redirects=True,
        **kwargs,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma exam-registration flow redirected back to login.")
    return response


def _get_authenticated_html(client: "AlmaClient", url: str) -> "requests.Response":
    response = client.session.get(url, timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma page redirected back to login.")
    return response


def _normalize_source_url(client: "AlmaClient", source_url: str | None) -> str:
    normalized = (source_url or client.timetable_url).strip()
    if not normalized:
        normalized = client.timetable_url
    if not urlparse(normalized).scheme:
        normalized = urljoin(f"{client.base_url}/", normalized)
    parsed = urlparse(normalized)
    base = urlparse(client.base_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc or not parsed.path.startswith("/alma/"):
        raise AlmaParseError("Alma exam-registration URLs must belong to the configured Alma host.")
    return normalized
