from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from .alma_portal_messages_models import AlmaPortalMessageItem, AlmaPortalMessagesPage
from .config import AlmaParseError
from .html_forms import extract_form_payload


def _clean_text(value: str) -> str:
    return " ".join(value.split())


@dataclass(frozen=True)
class AlmaPortalMessagesExpandRequest:
    action_url: str
    payload: dict[str, str]


@dataclass(frozen=True)
class AlmaPortalMessagesListContract:
    page_url: str
    action_url: str
    form_id: str
    payload: dict[str, str]
    toggle_trigger_name: str | None
    section_id: str | None
    partial_render_ids: tuple[str, ...]


def extract_portal_messages_list_contract(html: str, page_url: str) -> AlmaPortalMessagesListContract:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", attrs={"id": "startPage"})
    if form is None:
        raise AlmaParseError("Could not find the Alma start-page form.")

    form_id = form.get("id", "").strip()
    action_url = urljoin(page_url, form.get("action", page_url))
    trigger = _find_messages_toggle(form)
    section_id = _section_id_from_trigger(trigger)
    render_ids = [value for value in (section_id, _messages_infobox_id(form)) if value]

    return AlmaPortalMessagesListContract(
        page_url=page_url,
        action_url=action_url,
        form_id=form_id,
        payload=extract_form_payload(form),
        toggle_trigger_name=trigger,
        section_id=section_id,
        partial_render_ids=tuple(render_ids),
    )


def parse_portal_messages_page(html: str, page_url: str) -> AlmaPortalMessagesPage:
    return AlmaPortalMessagesPage(page_url=page_url, items=tuple(_parse_items(html, page_url)))


def parse_portal_messages_partial_response(response_text: str, page_url: str) -> AlmaPortalMessagesPage:
    if "<partial-response" not in response_text:
        return parse_portal_messages_page(response_text, page_url)
    try:
        root = ET.fromstring(response_text)
    except ET.ParseError as exc:
        raise AlmaParseError("Could not parse the Alma portal-messages partial response.") from exc
    updates = [update.text or "" for update in root.findall(".//update")]
    target_html = next((content for content in updates if "portalMessagesContent" in content), "")
    if not target_html:
        target_html = next((content for content in updates if "Meine Meldungen" in content), "")
    if not target_html:
        raise AlmaParseError("The Alma portal-messages response did not contain the messages list.")
    return parse_portal_messages_page(target_html, page_url)


def build_expand_portal_messages_request(
    contract: AlmaPortalMessagesListContract,
) -> AlmaPortalMessagesExpandRequest | None:
    if not contract.toggle_trigger_name or not contract.partial_render_ids:
        return None
    payload = dict(contract.payload)
    payload[contract.form_id] = contract.form_id
    payload["activePageElementId"] = contract.toggle_trigger_name
    payload["javax.faces.behavior.event"] = "action"
    payload["javax.faces.partial.event"] = "click"
    payload["javax.faces.source"] = contract.toggle_trigger_name
    payload["javax.faces.partial.ajax"] = "true"
    payload["javax.faces.partial.execute"] = contract.form_id
    payload["javax.faces.partial.render"] = " ".join(contract.partial_render_ids)
    return AlmaPortalMessagesExpandRequest(action_url=contract.action_url, payload=payload)


def _parse_items(html: str, page_url: str) -> list[AlmaPortalMessageItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[AlmaPortalMessageItem] = []
    for row in soup.select(".portalMessagesContent li"):
        link = row.select_one("a[href]")
        title_node = row.select_one(".portalMessageText")
        title = _clean_text(title_node.get_text(" ", strip=True) if title_node else row.get_text(" ", strip=True))
        if not title:
            continue
        date_label = _clean_text(row.select_one(".menuListDate").get_text(" ", strip=True)) if row.select_one(".menuListDate") else None
        remove_button = row.find(attrs={"onclick": lambda value: bool(value and "messageId" in value)})
        raw_remove = remove_button.get("onclick", "") if remove_button else ""
        message_id = _message_id(raw_remove) or (link.get("id", "").strip() if link else "") or title
        icon = row.find("img", src=True)
        href = link.get("href", "").strip() if link else ""
        icon_src = icon.get("src", "").strip() if icon else ""
        items.append(
            AlmaPortalMessageItem(
                id=message_id,
                title=title,
                url=urljoin(page_url, href) if href else None,
                target=(link.get("target", "").strip() or None) if link else None,
                icon_url=urljoin(page_url, icon_src) if icon_src else None,
                created_at=_parse_created_at(date_label),
                created_at_label=date_label,
            )
        )
    return items


def _find_messages_toggle(form) -> str | None:
    trigger = form.find(
        attrs={
            "id": lambda value: bool(value and ":titlemin_portletInstanceId_" in value),
            "title": lambda value: bool(value and "Meine Meldungen" in value),
        }
    )
    if trigger is None:
        trigger = form.find(
            attrs={
                "name": lambda value: bool(value and ":min_portletInstanceId_" in value),
                "title": lambda value: bool(value and "Meine Meldungen" in value),
            }
        )
    return (trigger.get("id") or trigger.get("name") or "").strip() if trigger else None


def _section_id_from_trigger(trigger: str | None) -> str | None:
    if not trigger:
        return None
    prefix = trigger.split(":titlemin_", 1)[0].split(":min_", 1)[0]
    suffix = trigger.rsplit("_", 1)[-1]
    return f"{prefix}:portletInstanceId_{suffix}"


def _messages_infobox_id(form) -> str | None:
    infobox = form.find(id=lambda value: bool(value and value.endswith(":messages-infobox")))
    return infobox.get("id", "").strip() if infobox else None


def _message_id(onclick: str) -> str | None:
    match = re.search(r"'messageId'\s*:\s*'([^']+)'", onclick)
    return match.group(1) if match else None


def _parse_created_at(label: str | None) -> datetime | None:
    if not label:
        return None
    cleaned = label.replace("Uhr", "").replace("-", " ").strip()
    try:
        return datetime.strptime(cleaned, "%d.%m.%Y %H:%M")
    except ValueError:
        return None
