from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .hsp_models import HspBookingOption, HspCourse, HspCourseSearchResult, HspLocation, HspOfferPage, HspPrice, HspScheduleSlot


def parse_hsp_course_search_data(
    javascript: str,
    source_url: str,
    *,
    query: str = "",
    area: str | None = None,
    include_unavailable: bool = False,
    limit: int = 50,
) -> HspCourseSearchResult:
    payload = _parse_search_payload(javascript)
    locations = payload.get("orte", [])
    days = payload.get("tage", [])
    areas = payload.get("bereiche", [])
    needle = _normalize(query)
    area_needle = _normalize(area or "")
    items: list[HspCourse] = []

    for row in payload.get("kurse", []):
        if not isinstance(row, list) or len(row) < 13 or int(row[0] or 0) <= 0:
            continue
        course_area = _safe_label(areas, _safe_int(row[12]))
        course = _map_course(row, locations, days, areas, source_url)
        searchable = " ".join(filter(None, [course.title, course.subtitle, course.instructor, course_area]))
        if needle and needle not in _normalize(searchable):
            continue
        if area_needle and area_needle not in _normalize(course_area):
            continue
        if not include_unavailable and not course.is_bookable:
            continue
        items.append(course)

    return HspCourseSearchResult(source_url=source_url, total_hits=len(items), items=items[:limit])


def parse_hsp_offer_page(html: str, source_url: str) -> HspOfferPage:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", action=lambda value: bool(value and "anmeldung.fcgi" in value))
    title = _node_text(soup.select_one(".bs_head")) or "Hochschulsport Angebot"
    responsible = _node_text(soup.select_one(".bs_verantw"))
    if responsible and responsible.startswith("verantwortlich:"):
        responsible = responsible.split(":", 1)[1].strip()

    return HspOfferPage(
        title=title,
        responsible=responsible,
        source_url=source_url,
        booking_form_action=urljoin(source_url, form.get("action")) if isinstance(form, Tag) else None,
        booking_code=_input_value(form, "BS_Code") if isinstance(form, Tag) else None,
        items=[_map_booking_option(block, source_url) for block in soup.select(".bs_angblock")],
    )


def hsp_offer_path(title: str) -> str:
    value = title
    for source, replacement in (
        ("&#196;", "Ae"),
        ("&#228;", "ae"),
        ("&#214;", "Oe"),
        ("&#246;", "oe"),
        ("&#220;", "Ue"),
        ("&#252;", "ue"),
        ("&#223;", "ss"),
        ("&amp;", "&"),
        ("Ä", "Ae"),
        ("ä", "ae"),
        ("Ö", "Oe"),
        ("ö", "oe"),
        ("Ü", "Ue"),
        ("ü", "ue"),
        ("ß", "ss"),
    ):
        value = value.replace(source, replacement)
    value = unescape(value).replace("&", " und ")
    value = re.sub(r"_+", "_", value)
    value = re.sub(r"[^A-Za-z0-9-]", "_", value)
    return "_" + value.lstrip("_") + ".html"


def _parse_search_payload(javascript: str) -> dict[str, object]:
    body = javascript.strip()
    if body.startswith("const data="):
        body = body[len("const data=") :]
    if body.endswith(";"):
        body = body[:-1]
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("HSP course search payload was not an object.")
    return parsed


def _map_course(row: list[object], locations: list[object], days: list[object], areas: list[object], source_url: str) -> HspCourse:
    title = _clean(row[2])
    subtitle = _clean(row[3]) or None
    date_range = _clean(row[7]) or None
    instructor = _clean(row[8]) or None
    price_summary, prices = _parse_prices(str(row[9] or ""))
    booking_start = _safe_int(row[11])
    return HspCourse(
        id=str(row[1]),
        title=title,
        subtitle=subtitle,
        area=_safe_label(areas, _safe_int(row[12])) or None,
        date_range=date_range,
        instructor=instructor,
        price_summary=price_summary,
        prices=prices,
        schedules=_map_schedules(row, locations, days),
        is_bookable=bool(_safe_int(row[10])),
        booking_starts_at=_format_epoch(booking_start),
        detail_url=urljoin(source_url, hsp_offer_path(title) + "#K" + str(row[1])),
    )


def _map_schedules(row: list[object], locations: list[object], days: list[object]) -> list[HspScheduleSlot]:
    slots: list[HspScheduleSlot] = []
    day_ids, times, location_ids = row[4], row[5], row[6]
    if not isinstance(day_ids, list) or not isinstance(times, list) or not isinstance(location_ids, list):
        return slots
    for day_id, time, location_id in zip(day_ids, times, location_ids):
        day = _safe_label(days, _safe_int(day_id))
        clean_time = _clean(time) or None
        location = _map_location(locations, _safe_int(location_id))
        if day or clean_time or location:
            slots.append(HspScheduleSlot(day=day or None, time=clean_time, location=location))
    return slots


def _map_location(locations: list[object], index: int) -> HspLocation | None:
    if index <= 0 or index >= len(locations) or not isinstance(locations[index], list):
        return None
    row = locations[index]
    return HspLocation(id=index, name=_clean(row[0]), latitude=_safe_float(row[1]), longitude=_safe_float(row[2]))


def _map_booking_option(block: Tag, source_url: str) -> HspBookingOption:
    detail_lines = [_node_text(node) for node in block.select("td.bs_sdet div.bs_tr")]
    title = detail_lines[1] if len(detail_lines) > 1 else _node_text(block.select_one("td.bs_sdet")) or ""
    course_id = _node_text(block.select_one("td.bs_sknr span")) or (block.get("id") or "").removeprefix("T")
    price_summary, prices = _parse_prices(str(block.select_one("td.bs_spreis") or ""))
    location_link = block.select_one("td.bs_sort a")
    info_link = block.select_one("td.bs_szr a")
    button = block.select_one("td.bs_sbuch input[type='submit']")
    return HspBookingOption(
        course_id=course_id,
        title=title,
        subtitle=_node_text(block.select_one("td.bs_sdet > span")) or None,
        location=_node_text(block.select_one("td.bs_sort")) or None,
        date_range=_node_text(block.select_one("td.bs_szr")) or None,
        instructor=_node_text(block.select_one("td.bs_skl")) or None,
        price_summary=price_summary,
        prices=prices,
        booking_label=button.get("value") if isinstance(button, Tag) else None,
        booking_submit_name=button.get("name") if isinstance(button, Tag) else None,
        booking_submit_value=button.get("value") if isinstance(button, Tag) else None,
        location_url=urljoin(source_url, location_link.get("href")) if isinstance(location_link, Tag) else None,
        info_url=urljoin(source_url, info_link.get("href")) if isinstance(info_link, Tag) else None,
    )


def _parse_prices(html: str) -> tuple[str | None, list[HspPrice]]:
    soup = BeautifulSoup(html, "html.parser")
    tiers: list[HspPrice] = []
    for row in soup.select(".bs_tr"):
        amount = _node_text(row.select_one(".bs_tt1"))
        audience = _node_text(row.select_one(".bs_tt2"))
        if amount and audience:
            tiers.append(HspPrice(amount=amount, audience=audience))
    summary = _node_text(soup.find("span")) or _node_text(soup)
    return summary or None, tiers


def _format_epoch(value: int) -> str | None:
    if value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _safe_label(values: list[object], index: int) -> str:
    if 0 <= index < len(values):
        value = values[index]
        if isinstance(value, list):
            return _clean(value[0])
        return _clean(value)
    return ""


def _input_value(form: Tag, name: str) -> str | None:
    node = form.find("input", attrs={"name": name})
    return node.get("value") if isinstance(node, Tag) else None


def _node_text(node: Tag | BeautifulSoup | None) -> str:
    if node is None:
        return ""
    return _clean(node.get_text(" ", strip=True))


def _clean(value: object) -> str:
    text = unescape(str(value or "")).replace("\xa0", " ")
    text = re.sub(r"<wbr\s*/?>", "", text)
    return re.sub(r"\s+", " ", BeautifulSoup(text, "html.parser").get_text(" ", strip=True)).strip()


def _normalize(value: str) -> str:
    return _clean(value).casefold()


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result or None
