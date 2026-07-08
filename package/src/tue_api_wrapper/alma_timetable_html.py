from __future__ import annotations

from datetime import datetime
from html import unescape
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .alma_availability import raise_for_alma_unavailable_page
from .alma_timetable_models import (
    AlmaTimetableContract,
    AlmaTimetableDay,
    AlmaTimetableFormRequest,
    AlmaTimetableOption,
)
from .config import AlmaParseError
from .html_forms import extract_form_payload


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _field_suffixes(field_name: str) -> tuple[str, ...]:
    parts = field_name.split(":")
    suffixes = [f":{parts[-1]}"]
    if len(parts) > 1:
        suffixes.insert(0, ":" + ":".join(parts[1:]))
    return tuple(dict.fromkeys(suffixes))


def _matches_field_name(expected_name: str):
    suffixes = _field_suffixes(expected_name)

    def matches(value: str | None) -> bool:
        if not value:
            return False
        return value == expected_name or any(value.endswith(suffix) for suffix in suffixes)

    return matches


def _find_named(root, tag_name: str | None, expected_name: str):
    matches = _matches_field_name(expected_name)
    if tag_name is None:
        return root.find(attrs={"name": matches}) or root.find(id=matches)
    return root.find(tag_name, attrs={"name": matches}) or root.find(tag_name, id=matches)


def _find_timetable_form(soup: BeautifulSoup):
    form = soup.find("form", attrs={"id": "plan"}) or soup.find(
        "form",
        attrs={"id": lambda value: bool(value and "individualTimetable" in value)},
    )
    if form is not None:
        return form

    for candidate in soup.find_all("form"):
        action = candidate.get("action", "")
        if "individualTimetable" in action:
            return candidate
        if _find_named(candidate, "select", "plan:scheduleConfiguration:anzeigeoptionen:changeTerm_input") is not None:
            return candidate
    return None


def _parse_select_options(soup: BeautifulSoup, field_name: str) -> tuple[AlmaTimetableOption, ...]:
    field = _find_named(soup, "select", field_name)
    if field is None:
        return ()

    options: list[AlmaTimetableOption] = []
    for option in field.find_all("option"):
        value = option.get("value", "").strip()
        label = option.get("data-title", "").strip() or _clean_text(option.get_text(" ", strip=True))
        if not value or not label:
            continue
        options.append(
            AlmaTimetableOption(
                value=value,
                label=label,
                is_selected=option.has_attr("selected"),
            )
        )
    return tuple(options)


def _selected_option(options: tuple[AlmaTimetableOption, ...]) -> AlmaTimetableOption | None:
    return next((option for option in options if option.is_selected), None)


def _parse_day_date(value: str) -> str | None:
    for token in value.split():
        try:
            return datetime.strptime(token, "%d.%m.%Y").date().isoformat()
        except ValueError:
            continue
    return None


def _extract_days(soup: BeautifulSoup) -> tuple[AlmaTimetableDay, ...]:
    days: list[AlmaTimetableDay] = []
    for column in soup.select("div.planFrame > ul.plan > li.column"):
        header = column.find("h2")
        label = _clean_text(header.get_text(" ", strip=True)) if header is not None else _clean_text(column.get("title", ""))
        if not label:
            continue

        restrict_button = column.find(
            attrs={"name": lambda value: bool(value and value.endswith(":showOnlyOneDay"))}
        ) or column.find(id=lambda value: bool(value and value.endswith(":showOnlyOneDay")))
        restrict_view_name = None
        if restrict_button is not None:
            restrict_view_name = restrict_button.get("name") or restrict_button.get("id")

        note = None
        column_head = column.find(class_="colhead")
        if column_head is not None:
            note_tokens = [
                token for token in (_clean_text(text) for text in column_head.stripped_strings) if token and token != label
            ]
            note = " ".join(note_tokens) or None

        days.append(
            AlmaTimetableDay(
                label=label,
                iso_date=_parse_day_date(column.get("title", "") or label),
                restrict_view_name=restrict_view_name,
                note=note,
            )
        )
    return tuple(days)


def _extract_export_url(soup: BeautifulSoup) -> str | None:
    field = _find_named(soup, "textarea", "plan:scheduleConfiguration:anzeigeoptionen:ical:cal_add")
    if field is None:
        return None
    value = field.get_text(strip=True) or field.get("data-page-permalink", "").strip()
    return unescape(value) if value else None


def build_timetable_action_request(
    html: str,
    page_url: str,
    *,
    trigger_name: str,
    field_overrides: dict[str, str] | None = None,
    extra_fields: dict[str, str] | None = None,
) -> AlmaTimetableFormRequest:
    soup = BeautifulSoup(html, "html.parser")
    form = _find_timetable_form(soup)
    if form is None:
        raise_for_alma_unavailable_page(html)
        raise AlmaParseError("Could not find the Alma timetable form.")

    trigger = _find_named(form, None, trigger_name)
    if trigger is None:
        raise AlmaParseError(f"Could not find Alma timetable trigger '{trigger_name}'.")
    actual_trigger_name = trigger.get("name") or trigger.get("id") or trigger_name

    payload = extract_form_payload(form)
    if field_overrides:
        for field_name, value in field_overrides.items():
            actual_field = _find_named(form, None, field_name)
            actual_name = actual_field.get("name") if actual_field is not None and actual_field.get("name") else field_name
            payload[actual_name] = value

    if "activePageElementId" in payload and not payload["activePageElementId"]:
        payload["activePageElementId"] = actual_trigger_name
    if "refreshButtonClickedId" in payload and not payload["refreshButtonClickedId"]:
        payload["refreshButtonClickedId"] = actual_trigger_name

    trigger_value = ""
    if trigger.name in {"button", "input"}:
        trigger_value = trigger.get("value", "")
        trigger_field_name = trigger.get("name") or actual_trigger_name
        payload[trigger_field_name] = trigger_value

    if extra_fields:
        payload.update(extra_fields)

    return AlmaTimetableFormRequest(
        page_url=page_url,
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
    )


def parse_timetable_contract(html: str, page_url: str) -> AlmaTimetableContract:
    soup = BeautifulSoup(html, "html.parser")

    terms = _parse_select_options(soup, "plan:scheduleConfiguration:anzeigeoptionen:changeTerm_input")
    range_modes = _parse_select_options(soup, "plan:scheduleConfiguration:anzeigeoptionen:auswahl_zeitraum_input")
    weeks = _parse_select_options(soup, "plan:scheduleConfiguration:anzeigeoptionen:selectWeek_input")
    days = _extract_days(soup)

    selected_term = _selected_option(terms)
    selected_range_mode = _selected_option(range_modes)
    selected_week = _selected_option(weeks)

    export_url = _extract_export_url(soup)
    print_available = _find_named(soup, None, "plan:scheduleConfiguration:anzeigeoptionen:print") is not None
    can_refresh_export_url = (
        _find_named(soup, None, "plan:scheduleConfiguration:anzeigeoptionen:ical:renewSecurityToken") is not None
    )
    supports_custom_range = any(option.value == "zeitraum" for option in range_modes)

    if not terms and not days and export_url is None:
        raise_for_alma_unavailable_page(html)
        raise AlmaParseError("The response did not look like an Alma timetable page.")

    return AlmaTimetableContract(
        page_url=page_url,
        terms=terms,
        range_modes=range_modes,
        weeks=weeks,
        days=days,
        selected_term_value=selected_term.value if selected_term is not None else None,
        selected_term_label=selected_term.label if selected_term is not None else None,
        selected_range_mode_value=selected_range_mode.value if selected_range_mode is not None else None,
        selected_range_mode_label=selected_range_mode.label if selected_range_mode is not None else None,
        selected_week_value=selected_week.value if selected_week is not None else None,
        selected_week_label=selected_week.label if selected_week is not None else None,
        export_url=export_url,
        print_available=print_available,
        can_refresh_export_url=can_refresh_export_url,
        supports_custom_range=supports_custom_range,
    )
