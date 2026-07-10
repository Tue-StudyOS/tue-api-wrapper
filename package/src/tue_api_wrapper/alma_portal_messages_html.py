from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from bs4 import BeautifulSoup

from .config import AlmaParseError
from .html_forms import extract_form_payload


def _clean_text(value: str) -> str:
    return " ".join(value.split())


@dataclass(frozen=True)
class AlmaPortalMessagesFormRequest:
    action_url: str
    payload: dict[str, str]


@dataclass(frozen=True)
class AlmaPortalMessagesStartPageContract:
    page_url: str
    action_url: str
    form_id: str
    payload: dict[str, str]
    configure_trigger_name: str
    container_id: str
    partial_render_ids: tuple[str, ...]


@dataclass(frozen=True)
class AlmaPortalMessagesSettingsState:
    feed_url: str | None
    renew_trigger_name: str | None
    renew_trigger_value: str | None
    view_state: str | None


def extract_portal_messages_start_page_contract(html: str, page_url: str) -> AlmaPortalMessagesStartPageContract:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", attrs={"id": "startPage"})
    if form is None:
        raise AlmaParseError("Could not find the Alma start-page form.")

    configure_button = form.find(
        "button",
        attrs={"name": lambda value: bool(value and value.endswith(":configurePortalMessages"))},
    )
    if configure_button is None:
        raise AlmaParseError("Could not find the Alma portal-messages settings trigger.")

    configure_trigger_name = configure_button.get("name", "").strip()
    if not configure_trigger_name:
        raise AlmaParseError("The Alma portal-messages settings trigger has no name.")

    portlet_prefix = configure_trigger_name.rsplit(":", 1)[0]
    container_id = f"{portlet_prefix}:portalMessagesContainer"
    if form.find(id=container_id) is None:
        container = form.find(id=lambda value: bool(value and value.endswith(":portalMessagesContainer")))
        if container is None:
            raise AlmaParseError("Could not find the Alma portal-messages container.")
        container_id = container.get("id", "").strip()
        if not container_id:
            raise AlmaParseError("The Alma portal-messages container has no id.")

    render_ids = [container_id]
    infobox = form.find(id=lambda value: bool(value and value.endswith(":messages-infobox")))
    if infobox is not None:
        infobox_id = infobox.get("id", "").strip()
        if infobox_id:
            render_ids.append(infobox_id)

    form_id = form.get("id", "").strip()
    if not form_id:
        raise AlmaParseError("The Alma start-page form has no id.")

    return AlmaPortalMessagesStartPageContract(
        page_url=page_url,
        action_url=urljoin(page_url, form.get("action", page_url)),
        form_id=form_id,
        payload=extract_form_payload(form),
        configure_trigger_name=configure_trigger_name,
        container_id=container_id,
        partial_render_ids=tuple(render_ids),
    )


def build_configure_portal_messages_request(
    contract: AlmaPortalMessagesStartPageContract,
) -> AlmaPortalMessagesFormRequest:
    payload = dict(contract.payload)
    payload[contract.form_id] = contract.form_id
    payload["javax.faces.behavior.event"] = "action"
    payload["javax.faces.partial.event"] = "click"
    payload["javax.faces.source"] = contract.configure_trigger_name
    payload["javax.faces.partial.ajax"] = "true"
    payload["javax.faces.partial.execute"] = contract.form_id
    payload["javax.faces.partial.render"] = " ".join(contract.partial_render_ids)
    return AlmaPortalMessagesFormRequest(action_url=contract.action_url, payload=payload)


def build_renew_portal_messages_request(
    contract: AlmaPortalMessagesStartPageContract,
    *,
    view_state: str | None,
    renew_trigger_name: str,
    renew_trigger_value: str | None,
) -> AlmaPortalMessagesFormRequest:
    payload = dict(contract.payload)
    payload[contract.form_id] = contract.form_id
    if view_state is not None:
        payload["javax.faces.ViewState"] = view_state
    payload[renew_trigger_name] = renew_trigger_value or ""
    payload["DISABLE_VALIDATION"] = "true"
    payload["DISABLE_AUTOSCROLL"] = "true"
    return AlmaPortalMessagesFormRequest(action_url=contract.action_url, payload=payload)


def _parse_settings_markup(html: str, page_url: str, *, view_state: str | None) -> AlmaPortalMessagesSettingsState:
    soup = BeautifulSoup(html, "html.parser")
    feed_link = soup.select_one(".portalMessagesSettings a.link_feed[href]") or soup.find(
        "a",
        attrs={"href": lambda value: bool(value and "portalMessagesFeed.faces" in value)},
    )
    renew_button = soup.find(
        "button",
        attrs={"name": lambda value: bool(value and value.endswith(":renewSecurityToken"))},
    ) or soup.find(
        "input",
        attrs={"name": lambda value: bool(value and value.endswith(":renewSecurityToken"))},
    )

    feed_url = None
    if feed_link is not None:
        href = feed_link.get("href", "").strip()
        if href:
            feed_url = urljoin(page_url, unescape(href))

    renew_trigger_name = None
    renew_trigger_value = None
    if renew_button is not None:
        renew_trigger_name = renew_button.get("name", "").strip() or None
        renew_trigger_value = renew_button.get("value", "").strip() or _clean_text(
            renew_button.get_text(" ", strip=True)
        )
        if not renew_trigger_value:
            renew_trigger_value = None

    if feed_url is None and renew_trigger_name is None:
        raise AlmaParseError("The response did not expose Alma portal-messages feed settings.")

    return AlmaPortalMessagesSettingsState(
        feed_url=feed_url,
        renew_trigger_name=renew_trigger_name,
        renew_trigger_value=renew_trigger_value,
        view_state=view_state,
    )


def parse_portal_messages_settings(
    response_text: str,
    page_url: str,
    *,
    container_id: str | None = None,
) -> AlmaPortalMessagesSettingsState:
    if "<partial-response" not in response_text:
        return _parse_settings_markup(response_text, page_url, view_state=None)

    try:
        root = ET.fromstring(response_text)
    except (ET.ParseError, DefusedXmlException) as exc:
        raise AlmaParseError("Could not parse the Alma portal-messages partial response.") from exc

    updates = {
        update.get("id", "").strip(): (update.text or "")
        for update in root.findall(".//update")
    }
    target_html = updates.get(container_id or "", "")
    if not target_html:
        target_html = next(
            (content for content in updates.values() if "portalMessagesFeed.faces" in content),
            "",
        )
    if not target_html:
        raise AlmaParseError("The Alma portal-messages partial response did not contain the settings panel.")

    view_state = next(
        (
            _clean_text(content)
            for update_id, content in updates.items()
            if "javax.faces.ViewState" in update_id and _clean_text(content)
        ),
        None,
    )
    return _parse_settings_markup(target_html, page_url, view_state=view_state)
