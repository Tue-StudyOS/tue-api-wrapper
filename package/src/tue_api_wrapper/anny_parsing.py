from __future__ import annotations

from typing import Any

from .anny_models import (
    AnnyAvailabilityDate,
    AnnyAvailabilityPeriod,
    AnnyBookingQuote,
    AnnyCalendarEvent,
    AnnyResource,
    AnnyResourcePage,
    AnnyResourceProperty,
    AnnyService,
    AnnyServiceConfiguration,
    AnnyTimeSlot,
)


def parse_resource_page(payload: dict[str, Any], *, source_url: str) -> AnnyResourcePage:
    page = payload.get("meta", {}).get("page", {})
    included = _included_map(payload)
    return AnnyResourcePage(
        source_url=source_url,
        total_results=_int(page.get("total")) or 0,
        total_pages=_int(page.get("last-page")) or 1,
        current_page=_int(page.get("current-page")) or 1,
        items=[_resource_from_json_api(item, included, source_url=None) for item in as_list(payload.get("data"))],
    )


def parse_resource_detail(payload: dict[str, Any], *, source_url: str) -> AnnyResource:
    return _resource_from_json_api(payload.get("data", {}), _included_map(payload), source_url=source_url)


def parse_service_configuration(
    payload: dict[str, Any],
    *,
    resource_id: str,
    service_id: str,
) -> AnnyServiceConfiguration:
    data = payload.get("data", {})
    attrs = data.get("attributes", {}) if isinstance(data, dict) else {}
    service = _first_service(attrs.get("services_with_quantity"), service_id)
    return AnnyServiceConfiguration(
        resource_id=resource_id,
        service_id=service_id,
        name=_text(service.get("name") or attrs.get("label")),
        next_available_date=_text(payload.get("meta", {}).get("next_available_date")),
        min_duration=_int(attrs.get("min_duration")),
        max_duration=_int(attrs.get("max_duration")),
        calculation_interval=_int(attrs.get("calculation_interval")),
        advance_booking_period=_int(attrs.get("advance_booking_period")),
        duration_label=_text(attrs.get("duration_label")),
        price_label=_text(attrs.get("price_label")),
        is_free=attrs.get("is_free") if isinstance(attrs.get("is_free"), bool) else None,
        currency=_text(attrs.get("currency")),
    )


def parse_time_slot(item: dict[str, Any]) -> AnnyTimeSlot:
    return AnnyTimeSlot(
        start_date=str(item.get("start_date") or ""),
        end_date=str(item.get("end_date") or ""),
        available=bool(item.get("available")),
        unit=_text(item.get("unit")),
        quota=_int(item.get("quota")),
        remaining_number_available=_int(item.get("remaining_number_available")),
        unavailability_type=_text(item.get("unavailability_type")),
        messages=[str(message) for message in as_list(item.get("messages"))],
    )


def parse_availability_date(item: dict[str, Any]) -> AnnyAvailabilityDate:
    return AnnyAvailabilityDate(
        date=str(item.get("date") or ""),
        available=bool(item.get("available")),
        timezone=_text(item.get("timezone")),
        unavailability_type=_text(item.get("unavailability_type")),
    )


def parse_availability_period(item: dict[str, Any], *, resource_id: str) -> AnnyAvailabilityPeriod:
    return AnnyAvailabilityPeriod(
        id=str(item.get("id") or ""),
        resource_id=resource_id,
        start_date=str(item.get("start_date") or ""),
        end_date=str(item.get("end_date") or ""),
        quota=_int(item.get("quota")),
        title=_text(item.get("title")),
    )


def parse_calendar_event(item: dict[str, Any]) -> AnnyCalendarEvent:
    availability = item.get("resource_availability_result", {})
    intervals = []
    for result in as_list(availability.get("serviceAvailabilityResults")):
        intervals.extend(parse_time_slot(slot) for slot in as_list(result.get("available_intervals")))
    return AnnyCalendarEvent(
        id=str(item.get("id") or ""),
        resource_id=str(item.get("resource_id") or ""),
        resource_name=_text(item.get("resource_name")),
        start_date=str(item.get("start_date") or ""),
        end_date=str(item.get("end_date") or ""),
        is_available=bool(item.get("is_available")),
        display_label=_text(item.get("display_label")),
        occupancy=_int(item.get("occupancy")),
        quota=_int(item.get("quota")),
        available_intervals=intervals,
    )


def parse_booking_quote(payload: dict[str, Any], *, resource_id: str, service_id: str) -> AnnyBookingQuote:
    total = payload.get("total")
    return AnnyBookingQuote(
        resource_id=resource_id,
        service_id=service_id,
        start_date=_text(payload.get("start_date")),
        end_date=_text(payload.get("end_date")),
        charged_duration=_int(payload.get("charged_duration")),
        total=total if isinstance(total, int | float) else None,
        currency=_text(payload.get("currency")),
        price_hidden=payload.get("price_hidden") if isinstance(payload.get("price_hidden"), bool) else None,
        items=[
            str(item.get("title"))
            for item in as_list(payload.get("items"))
            if isinstance(item, dict) and item.get("title")
        ],
    )


def resource_search_text(item: AnnyResource) -> str:
    return " ".join(
        part for part in (item.name, item.slug, item.description or "", item.location or "") if part
    ).casefold()


def as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _resource_from_json_api(
    item: dict[str, Any],
    included: dict[tuple[str, str], dict[str, Any]],
    *,
    source_url: str | None,
) -> AnnyResource:
    attrs = item.get("attributes", {}) if isinstance(item, dict) else {}
    relationships = item.get("relationships", {}) if isinstance(item, dict) else {}
    return AnnyResource(
        id=str(item.get("id") or ""),
        slug=str(attrs.get("slug") or ""),
        name=str(attrs.get("name") or ""),
        source_url=source_url,
        description=_text(attrs.get("plain_description") or attrs.get("description")),
        category=_related_attribute(relationships, included, "category", "name"),
        location=_related_meta_or_attribute(relationships, included, "location", "address_line", "name"),
        image_url=_image_url(_related(relationships, included, "cover_image")),
        timezone=_text(attrs.get("timezone")),
        quantity=_int(attrs.get("quantity")),
        bookings_enabled=bool(attrs.get("bookings_enabled")),
        booking_requires_community=bool(attrs.get("booking_requires_community")),
        viewing_requires_community=bool(attrs.get("viewing_requires_community")),
        services=_services(relationships, included),
        properties=_properties(relationships, included),
    )


def _included_map(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(item.get("type")), str(item.get("id"))): item
        for item in as_list(payload.get("included"))
        if isinstance(item, dict)
    }


def _related(
    relationships: dict[str, Any],
    included: dict[tuple[str, str], dict[str, Any]],
    name: str,
) -> dict[str, Any] | None:
    data = relationships.get(name, {}).get("data") if isinstance(relationships.get(name), dict) else None
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        return None
    return included.get((str(data.get("type")), str(data.get("id"))))


def _related_attribute(
    relationships: dict[str, Any],
    included: dict[tuple[str, str], dict[str, Any]],
    name: str,
    attribute: str,
) -> str | None:
    item = _related(relationships, included, name)
    return _text(item.get("attributes", {}).get(attribute)) if item else None


def _related_meta_or_attribute(
    relationships: dict[str, Any],
    included: dict[tuple[str, str], dict[str, Any]],
    name: str,
    meta_key: str,
    attribute: str,
) -> str | None:
    rel = relationships.get(name, {})
    meta_value = rel.get("data", {}).get("meta", {}).get(meta_key) if isinstance(rel.get("data"), dict) else None
    return _text(meta_value) or _related_attribute(relationships, included, name, attribute)


def _services(relationships: dict[str, Any], included: dict[tuple[str, str], dict[str, Any]]) -> list[AnnyService]:
    result = []
    service_rel = relationships.get("services", {})
    for data in as_list(service_rel.get("data") if isinstance(service_rel, dict) else None):
        item = included.get((str(data.get("type")), str(data.get("id"))), {})
        attrs = item.get("attributes", {})
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        result.append(
            AnnyService(
                id=str(data.get("id") or ""),
                name=_text(attrs.get("name")),
                slug=_text(attrs.get("slug")),
                duration_label=_text(meta.get("duration_preview")),
                supports_instant_booking=meta.get("supports_instant_booking")
                if isinstance(meta.get("supports_instant_booking"), bool)
                else None,
                min_duration=_int(attrs.get("min_duration")),
                max_duration=_int(attrs.get("max_duration")),
                booking_interval=_int(attrs.get("booking_interval")),
            )
        )
    return result


def _properties(
    relationships: dict[str, Any],
    included: dict[tuple[str, str], dict[str, Any]],
) -> list[AnnyResourceProperty]:
    result = []
    property_rel = relationships.get("resource_properties", {})
    for data in as_list(property_rel.get("data") if isinstance(property_rel, dict) else None):
        item = included.get((str(data.get("type")), str(data.get("id"))), {})
        prop_ref = item.get("relationships", {}).get("property", {}).get("data", {})
        prop = included.get((str(prop_ref.get("type")), str(prop_ref.get("id"))), {})
        attrs = prop.get("attributes", {})
        label = _text(attrs.get("label"))
        if label:
            result.append(
                AnnyResourceProperty(
                    id=str(data.get("id") or ""),
                    label=label,
                    value=item.get("attributes", {}).get("value"),
                    private=bool(attrs.get("private")),
                )
            )
    return result


def _first_service(services_with_quantity: object, service_id: str) -> dict[str, Any]:
    for item in as_list(services_with_quantity):
        service = item.get("service") if isinstance(item, dict) else None
        if isinstance(service, dict) and str(service.get("id")) == service_id:
            return service
    return {}


def _image_url(item: dict[str, Any] | None) -> str | None:
    attrs = item.get("attributes", {}) if item else {}
    return _text(attrs.get("medium_path") or attrs.get("url"))


def _int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
