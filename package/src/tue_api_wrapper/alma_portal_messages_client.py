from __future__ import annotations

from .alma_portal_messages_html import (
    AlmaPortalMessagesStartPageContract,
    AlmaPortalMessagesSettingsState,
    build_configure_portal_messages_request,
    build_renew_portal_messages_request,
    extract_portal_messages_start_page_contract,
    parse_portal_messages_settings,
)
from .alma_portal_messages_items_html import (
    build_expand_portal_messages_request,
    extract_portal_messages_list_contract,
    parse_portal_messages_page,
    parse_portal_messages_partial_response,
)
from .alma_portal_messages_models import AlmaPortalMessagesFeed, AlmaPortalMessagesPage
from .client import AlmaClient
from .config import AlmaLoginError, AlmaParseError


def _fetch_start_page(client: AlmaClient) -> tuple[str, str]:
    response = client.session.get(
        client.start_page_url,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma start page redirected back to login.")
    return response.text, response.url


def _post_form(client: AlmaClient, *, action_url: str, payload: dict[str, str]) -> tuple[str, str]:
    response = client.session.post(
        action_url,
        data=payload,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma portal-messages action redirected back to login.")
    return response.text, response.url


def _open_portal_messages_settings(
    client: AlmaClient,
) -> tuple[AlmaPortalMessagesStartPageContract, AlmaPortalMessagesSettingsState]:
    html, page_url = _fetch_start_page(client)
    contract = extract_portal_messages_start_page_contract(html, page_url)
    request = build_configure_portal_messages_request(contract)
    response_text, response_url = _post_form(client, action_url=request.action_url, payload=request.payload)
    settings = parse_portal_messages_settings(
        response_text,
        response_url,
        container_id=contract.container_id,
    )
    return contract, settings


def _build_feed_result(
    contract: AlmaPortalMessagesStartPageContract,
    settings: AlmaPortalMessagesSettingsState,
) -> AlmaPortalMessagesFeed:
    if settings.feed_url is None:
        raise AlmaParseError("Alma did not expose a portal-messages RSS feed URL.")
    return AlmaPortalMessagesFeed(
        page_url=contract.page_url,
        feed_url=settings.feed_url,
        can_refresh_feed=settings.renew_trigger_name is not None,
    )


def fetch_portal_messages_feed(client: AlmaClient) -> AlmaPortalMessagesFeed:
    contract, settings = _open_portal_messages_settings(client)
    return _build_feed_result(contract, settings)


def fetch_portal_messages(client: AlmaClient) -> AlmaPortalMessagesPage:
    html, page_url = _fetch_start_page(client)
    page = parse_portal_messages_page(html, page_url)
    if page.items:
        return page

    contract = extract_portal_messages_list_contract(html, page_url)
    request = build_expand_portal_messages_request(contract)
    if request is None:
        return page

    response_text, response_url = _post_form(client, action_url=request.action_url, payload=request.payload)
    return parse_portal_messages_partial_response(response_text, response_url)


def refresh_portal_messages_feed(client: AlmaClient) -> AlmaPortalMessagesFeed:
    contract, settings = _open_portal_messages_settings(client)
    if settings.renew_trigger_name is None:
        raise AlmaParseError("Alma did not expose a portal-messages feed refresh action.")

    renew_request = build_renew_portal_messages_request(
        contract,
        view_state=settings.view_state,
        renew_trigger_name=settings.renew_trigger_name,
        renew_trigger_value=settings.renew_trigger_value,
    )
    _post_form(client, action_url=renew_request.action_url, payload=renew_request.payload)

    refreshed_contract, refreshed_settings = _open_portal_messages_settings(client)
    return _build_feed_result(refreshed_contract, refreshed_settings)
