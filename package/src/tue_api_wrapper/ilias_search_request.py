from __future__ import annotations

from .config import AlmaParseError


def search_payload(contract, term: str, *, search_mode: str | None = None,
                   content_types: tuple[str, ...] = (), created_enabled: bool = False,
                   created_mode: str | None = None, created_date: str | None = None) -> dict[str, str]:
    if not term.strip():
        raise AlmaParseError("A non-empty ILIAS search term is required.")
    payload = dict(contract.payload)
    payload[contract.term_field_name] = term.strip()
    if search_mode:
        payload[contract.search_mode_field_name] = search_mode
    for option in contract.filters.content_types:
        payload.pop(f"filter_type[{option.value}]", None)
    for value in dict.fromkeys(value.strip() for value in content_types if value.strip()):
        payload[f"filter_type[{value}]"] = "1"
    if created_enabled:
        payload[contract.creation_enabled_field_name] = "1"
        if created_mode:
            payload[contract.creation_mode_field_name] = created_mode
        if created_date:
            payload[contract.creation_date_field_name] = created_date
    else:
        payload.pop(contract.creation_enabled_field_name, None)
    payload[contract.search_button_name] = "Suche"
    return payload
