from __future__ import annotations

import xml.etree.ElementTree as ET

from .config import AlmaParseError


def extract_partial_updates(response_text: str) -> tuple[tuple[str, str], ...]:
    if "<partial-response" not in response_text:
        return ()
    try:
        root = ET.fromstring(response_text.lstrip())
    except ET.ParseError as exc:
        raise AlmaParseError("Could not parse the Alma partial response.") from exc
    return tuple(
        (update.get("id", "").strip(), update.text or "")
        for update in root.findall(".//update")
    )


def select_partial_markup(response_text: str, *needles: str) -> str:
    updates = extract_partial_updates(response_text)
    if not updates:
        return response_text
    for _update_id, content in updates:
        if all(needle in content for needle in needles):
            return content
    for _update_id, content in updates:
        if any(needle in content for needle in needles):
            return content
    return "\n".join(content for _update_id, content in updates if content)
