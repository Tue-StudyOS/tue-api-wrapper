from __future__ import annotations

from .alma_documents_html import extract_studyservice_page
from .alma_studyservice_models import AlmaStudyServicePage, AlmaStudyServiceTab
from .config import AlmaLoginError, AlmaParseError

DOCUMENTS_TAB_LABEL = "Bescheide"


def fetch_studyservice_contract(client, *, tab_label: str | None = None) -> AlmaStudyServicePage:
    response = client.session.get(client.studyservice_url, timeout=client.timeout_seconds)
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the study service page redirected back to login.")

    page = extract_studyservice_page(response.text, response.url)
    if (
        tab_label is None
        or _matches_tab(page.active_tab_label, tab_label)
        or (_matches_tab(DOCUMENTS_TAB_LABEL, tab_label) and _has_document_content(page))
    ):
        return page
    return _post_studyservice_tab(client, page, tab_label=tab_label)


def fetch_studyservice_documents_contract(client) -> AlmaStudyServicePage:
    return fetch_studyservice_contract(client, tab_label=DOCUMENTS_TAB_LABEL)


def _post_studyservice_tab(client, page: AlmaStudyServicePage, *, tab_label: str) -> AlmaStudyServicePage:
    tab = _find_tab(page.tabs, tab_label)
    payload = dict(page.payload)
    payload["activePageElementId"] = tab.button_name
    payload["refreshButtonClickedId"] = ""
    payload[tab.button_name] = _clean_active_label(tab.label)
    payload["studyserviceForm:_idcl"] = tab.button_name
    payload.setdefault("DISABLE_VALIDATION", "true")
    payload.setdefault("DISABLE_AUTOSCROLL", "true")

    response = client.session.post(
        page.action_url,
        data=payload,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the study service tab request redirected back to login.")
    return extract_studyservice_page(response.text, response.url)


def _find_tab(tabs: tuple[AlmaStudyServiceTab, ...], label: str) -> AlmaStudyServiceTab:
    tab = next((item for item in tabs if _matches_tab(item.label, label)), None)
    if tab is None:
        labels = ", ".join(item.label for item in tabs) or "none"
        raise AlmaParseError(f"Could not find Alma study-service tab matching '{label}'. Available tabs: {labels}")
    return tab


def _matches_tab(actual: str | None, expected: str) -> bool:
    if actual is None:
        return False
    return expected.casefold() in _clean_active_label(actual).casefold()


def _has_document_content(page: AlmaStudyServicePage) -> bool:
    return bool(page.reports or page.output_requests or page.latest_download_url)


def _clean_active_label(label: str) -> str:
    return " ".join(label.replace("Aktive Registerkarte", "").split())
