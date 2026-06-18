from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .alma_enrollment_html import TERM_FIELD, parse_enrollment_page
from .alma_official_documents import _document_if_ready, _find_document_link, _resolve_report
from .alma_partial import select_partial_markup
from .config import AlmaLoginError, AlmaParseError
from .html_forms import extract_form_payload
from .models import AlmaDocumentReport, AlmaDownloadedDocument, AlmaEnrollmentPage

ENROLLMENT_URL = (
    "/alma/pages/cm/exa/enrollment/info/start.xhtml"
    "?_flowId=searchOwnEnrollmentInfo-flow"
    "&navigationPosition=hisinoneMeinStudium%2ChisinoneOwnEnrollmentList"
    "&recordRequest=true"
)
TERM_REFRESH_TRIGGER = "studentOverviewForm:enrollmentsDiv:termSelector:refresh"


@dataclass(frozen=True)
class AlmaEnrollmentContract:
    page_url: str
    action_url: str
    payload: dict[str, str]
    enctype: str | None
    terms: dict[str, str]
    selected_term: str | None
    reports: tuple[AlmaDocumentReport, ...]


def fetch_enrollment_page(client, *, term: str | None = None) -> AlmaEnrollmentPage:
    contract, html, page_url = _fetch_enrollment_contract(client)
    term_value = _resolve_term_value(contract, term)
    if term_value is None or term_value == contract.payload.get(TERM_FIELD):
        return parse_enrollment_page(html, page_url)

    response = _post_enrollment_action(
        client,
        contract,
        field_overrides={TERM_FIELD: term_value},
        trigger_name=TERM_REFRESH_TRIGGER,
        extra_fields={"DISABLE_VALIDATION": "true"},
    )
    if "<partial-response" not in response.text:
        return parse_enrollment_page(response.text, response.url)
    return parse_enrollment_page(_merge_partial_enrollment_markup(contract, response.text, term_value), response.url)


def list_enrollment_reports(client) -> tuple[AlmaDocumentReport, ...]:
    contract, _html, _page_url = _fetch_enrollment_contract(client)
    return contract.reports


def download_enrollment_report(
    client,
    *,
    trigger_name: str | None = None,
    term: str | None = None,
    poll_attempts: int = 3,
) -> AlmaDownloadedDocument:
    contract, _html, _page_url = _fetch_enrollment_contract(client)
    term_value = _resolve_term_value(contract, term)
    if term_value is not None and term_value != contract.payload.get(TERM_FIELD):
        response = _post_enrollment_action(
            client,
            contract,
            field_overrides={TERM_FIELD: term_value},
            trigger_name=TERM_REFRESH_TRIGGER,
            extra_fields={"DISABLE_VALIDATION": "true"},
        )
        if "<partial-response" not in response.text:
            contract = _parse_enrollment_contract(response.text, response.url)
        else:
            contract = _parse_enrollment_contract(
                _merge_partial_enrollment_markup(contract, response.text, term_value),
                response.url,
            )

    report = _resolve_report(contract.reports, trigger_name, kind="enrollment report")
    response = _post_enrollment_action(client, contract, trigger_name=report.trigger_name)
    document = _document_if_ready(client, response)
    if document is not None:
        return document
    link = _find_document_link(response.text, response.url)
    if link is not None:
        return client._download_document(link)
    return _poll_enrollment_report(client, contract, response.text, response.url, attempts=poll_attempts)


def _fetch_enrollment_contract(client) -> tuple[AlmaEnrollmentContract, str, str]:
    response = client.session.get(
        f"{client.base_url}{ENROLLMENT_URL}",
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the enrollment page redirected back to login.")
    return _parse_enrollment_contract(response.text, response.url), response.text, response.url


def _parse_enrollment_contract(html: str, page_url: str) -> AlmaEnrollmentContract:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="studentOverviewForm")
    if form is None:
        raise AlmaParseError("Could not find the Alma enrollment overview form.")
    page = parse_enrollment_page(html, page_url)
    reports = []
    seen = set()
    for node in form.find_all(attrs={"name": lambda value: bool(value and "enrollStudentListJobConfigurationButtons" in value and value.endswith(":job2"))}):
        trigger = node.get("name")
        if not trigger or trigger in seen:
            continue
        seen.add(trigger)
        label = " ".join(node.get_text(" ", strip=True).split()) or node.get("value") or trigger.rsplit(":", 1)[-1]
        reports.append(AlmaDocumentReport(label=label, trigger_name=trigger))
    return AlmaEnrollmentContract(
        page_url=page_url,
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=extract_form_payload(form),
        enctype=form.get("enctype"),
        terms=page.available_terms,
        selected_term=page.selected_term,
        reports=tuple(reports),
    )


def _post_enrollment_action(
    client,
    contract: AlmaEnrollmentContract,
    *,
    trigger_name: str,
    field_overrides: dict[str, str] | None = None,
    extra_fields: dict[str, str] | None = None,
):
    payload = dict(contract.payload)
    if field_overrides:
        payload.update(field_overrides)
    payload["activePageElementId"] = trigger_name
    payload["refreshButtonClickedId"] = ""
    payload[trigger_name] = payload.get(trigger_name, "")
    if extra_fields:
        payload.update(extra_fields)
    response = client.session.post(contract.action_url, data=payload, timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if not response.text.lstrip().startswith("<?xml") and client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the enrollment action redirected back to login.")
    return response


def _resolve_term_value(contract: AlmaEnrollmentContract, term: str | None) -> str | None:
    raw = (term or "").strip()
    if not raw:
        return None
    for label, value in contract.terms.items():
        if raw == value or raw.casefold() == label.casefold():
            return value
    available = ", ".join(contract.terms)
    raise AlmaParseError(f"Unknown Alma enrollment term '{term}'. Available terms: {available}")


def _merge_partial_enrollment_markup(contract: AlmaEnrollmentContract, response_text: str, selected_value: str) -> str:
    content = select_partial_markup(response_text, "termEnrollmentDiv")
    options = "\n".join(
        f'<option value="{escape(value)}"{" selected" if value == selected_value else ""}>{escape(label)}</option>'
        for label, value in contract.terms.items()
    )
    return f'<form id="studentOverviewForm"><select name="{TERM_FIELD}">{options}</select>{content}</form>'


def _poll_enrollment_report(client, contract: AlmaEnrollmentContract, html: str, page_url: str, *, attempts: int) -> AlmaDownloadedDocument:
    for _ in range(max(1, attempts)):
        trigger = _poll_trigger(html)
        response = _post_enrollment_action(client, contract, trigger_name=trigger)
        document = _document_if_ready(client, response)
        if document is not None:
            return document
        link = _find_document_link(response.text, page_url)
        if link is not None:
            return client._download_document(link)
        html = response.text
        page_url = response.url
    raise AlmaParseError("Alma did not expose the generated enrollment PDF after polling the report job.")


def _poll_trigger(html: str) -> str:
    soup = BeautifulSoup(select_partial_markup(html, "jobDownloadPoll"), "html.parser")
    button = soup.find(attrs={"name": lambda value: bool(value and value.endswith(":jobDownloadPoll:poll"))})
    if button is None:
        raise AlmaParseError("Alma did not expose an enrollment report polling action.")
    return button.get("name")
