from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from .alma_academics_html import parse_exam_overview
from .config import AlmaLoginError, AlmaParseError
from .html_forms import extract_form_payload
from .models import AlmaExamNode

if TYPE_CHECKING:
    from .client import AlmaClient


_FORM_ID = "examsReadonly"
_TREE_ID = (
    "examsReadonly:overviewAsTreeReadonly:tree:ExamOverviewForPersonTreeReadonly"
)
_MESSAGES_ID = "examsReadonly:messages-infobox"
_MAX_EXPANSIONS = 100


@dataclass(frozen=True)
class _ExamTreeContract:
    action_url: str
    payload: dict[str, str]
    fragment: str


def fetch_exam_overview(client: AlmaClient, page_url: str) -> tuple[AlmaExamNode, ...]:
    response = client.session.get(
        page_url,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError(
            "Session is not authenticated; the exam overview page redirected back "
            "to login."
        )

    contract = _extract_contract(response.text, response.url)
    payload = dict(contract.payload)
    fragment = contract.fragment
    expanded: set[str] = set()

    for _ in range(_MAX_EXPANSIONS):
        pending = _collapsed_triggers(fragment)
        trigger = next((name for name in pending if name not in expanded), None)
        if trigger is None:
            if pending:
                raise AlmaParseError("Alma did not expand the requested exam tree node.")
            return parse_exam_overview(_as_tree_table(fragment))

        partial = client.session.post(
            contract.action_url,
            data=_expand_payload(payload, trigger),
            timeout=client.timeout_seconds,
            allow_redirects=True,
        )
        partial.raise_for_status()
        if "<partial-response" not in partial.text and client._looks_logged_out(
            partial.text
        ):
            raise AlmaLoginError(
                "Session is not authenticated; the exam overview action redirected "
                "back to login."
            )
        fragment, view_state = _parse_partial_response(partial.text)
        if view_state is not None:
            payload["javax.faces.ViewState"] = view_state
        expanded.add(trigger)

    raise AlmaParseError("Alma exam tree exceeded the expansion safety limit.")


def _extract_contract(html: str, page_url: str) -> _ExamTreeContract:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id=_FORM_ID)
    if form is None:
        raise AlmaParseError("Could not find the Alma exam overview form.")
    tables = form.find_all("table", class_="treeTableWithIcons")
    table = next(
        (
            item
            for item in tables
            if item.find(
                attrs={
                    "id": lambda value: bool(value and _TREE_ID in value),
                }
            )
            is not None
        ),
        tables[0] if tables else None,
    )
    if table is None:
        raise AlmaParseError("Could not find the Alma exam overview tree table.")
    action = form.get("action")
    return _ExamTreeContract(
        action_url=urljoin(page_url, action or page_url),
        payload=extract_form_payload(form),
        fragment=str(table),
    )


def _collapsed_triggers(fragment: str) -> tuple[str, ...]:
    soup = BeautifulSoup(fragment, "html.parser")
    return tuple(
        button["name"]
        for button in soup.find_all(
            "button",
            class_="treeTableIcon",
            attrs={"aria-expanded": "false", "name": True},
        )
    )


def _expand_payload(payload: dict[str, str], trigger: str) -> dict[str, str]:
    expanded = dict(payload)
    expanded[_FORM_ID] = _FORM_ID
    expanded["activePageElementId"] = trigger
    expanded.update(
        {
            "javax.faces.behavior.event": "action",
            "javax.faces.partial.event": "click",
            "javax.faces.source": trigger,
            "javax.faces.partial.ajax": "true",
            "javax.faces.partial.execute": f"{_TREE_ID} ",
            "javax.faces.partial.render": f"{_TREE_ID} {_MESSAGES_ID} ",
        }
    )
    return expanded


def _parse_partial_response(response_text: str) -> tuple[str, str | None]:
    try:
        root = ET.fromstring(response_text)
    except (ET.ParseError, DefusedXmlException) as error:
        raise AlmaParseError(
            "Could not parse the Alma exam-tree response."
        ) from error
    updates = {
        update.attrib.get("id", ""): update.text or ""
        for update in root.findall(".//update")
    }
    fragment = updates.get(_TREE_ID)
    if fragment is None:
        raise AlmaParseError("The Alma response did not contain the exam tree.")
    view_state = next(
        (
            value
            for update_id, value in updates.items()
            if "javax.faces.ViewState" in update_id
        ),
        None,
    )
    return fragment, view_state


def _as_tree_table(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    if soup.find("table", class_="treeTableWithIcons") is not None:
        return fragment
    return f'<table class="treeTableWithIcons">{fragment}</table>'
