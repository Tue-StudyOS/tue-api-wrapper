from __future__ import annotations

import requests
from requests import Response

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
from .anny_parsing import (
    as_list,
    parse_availability_date,
    parse_availability_period,
    parse_booking_quote,
    parse_calendar_event,
    parse_resource_detail,
    parse_resource_page,
    parse_service_configuration,
    parse_time_slot,
    resource_search_text,
)
from .config import DEFAULT_TIMEOUT_SECONDS

ANNY_API_URL = "https://b.anny.eu/api/v1"
ANNY_ORIGIN = "https://anny.eu"
ANNY_APP_KEY = "anny_shop"
DEFAULT_ANNY_ORGANIZATION_SLUG = "universitaetsbibliothek-tuebingen"
DEFAULT_ANNY_CATEGORY_ID = "596"
DEFAULT_ANNY_TIMEZONE = "Europe/Berlin"

RESOURCE_LIST_INCLUDE = "category,cover_image,resource_properties.property,services,organization,location,communities"
RESOURCE_DETAIL_INCLUDE = (
    "cover_image,schedules,gallery_images,organization.address,organization.logo_image,category,"
    "services.cancellation_policy,services.cover_image,resource_properties.property,services.group,"
    "location,communities,all_communities,files"
)
SERVICE_CONFIGURATION_INCLUDE = (
    "services.add_ons,services.add_ons.cover_image,services.add_ons.group,services.cover_image,"
    "services.service_sub_resources,main_service.add_ons,main_service.add_ons.cover_image,"
    "main_service.add_ons.group,main_service.cover_image,main_service.service_sub_resources"
)


class AnnyClient:
    def __init__(
        self,
        *,
        organization_slug: str = DEFAULT_ANNY_ORGANIZATION_SLUG,
        customer_account_id: str | None = None,
        auth_token: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.organization_slug = organization_slug
        self.customer_account_id = customer_account_id
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"x-app-key": ANNY_APP_KEY, "origin": ANNY_ORIGIN, "referer": f"{ANNY_ORIGIN}/"})
        if auth_token:
            self.session.headers["authorization"] = _bearer(auth_token)

    def list_resources(
        self,
        *,
        query: str = "",
        category_id: str = DEFAULT_ANNY_CATEGORY_ID,
        page: int = 1,
        page_size: int = 25,
    ) -> AnnyResourcePage:
        endpoint = self._resource_scope_path()
        params: list[tuple[str, str | int]] = [
            ("include", RESOURCE_LIST_INCLUDE),
            ("page[number]", page),
            ("page[size]", page_size),
            ("sort", "name"),
            ("stateless", "1"),
        ]
        if category_id:
            params.append(("filter[categories][]", category_id))
        response = self.session.get(f"{ANNY_API_URL}/{endpoint}/all-resources", params=params, timeout=self.timeout)
        result = parse_resource_page(_response_json(response), source_url=response.url)
        if query.strip():
            needle = query.strip().casefold()
            result.items = [item for item in result.items if needle in resource_search_text(item)]
            result.total_results = len(result.items)
        return result

    def fetch_resource(self, slug: str, *, visit_token: str | None = None) -> AnnyResource:
        params: dict[str, str] = {
            "include": RESOURCE_DETAIL_INCLUDE,
            "preview_token": "",
            "service_access_code": "",
        }
        if visit_token:
            params["visit_token"] = visit_token
        response = self.session.get(f"{ANNY_API_URL}/resources/{slug}", params=params, timeout=self.timeout)
        return parse_resource_detail(_response_json(response), source_url=response.url)

    def fetch_service_configuration(
        self,
        *,
        resource_id: str,
        service_id: str,
        timezone: str = DEFAULT_ANNY_TIMEZONE,
    ) -> AnnyServiceConfiguration:
        response = self.session.get(
            f"{ANNY_API_URL}/service-configuration",
            params=[
                ("include", SERVICE_CONFIGURATION_INCLUDE),
                (f"service_id[{service_id}]", "1"),
                ("resource_id", resource_id),
                ("timezone", timezone),
            ],
            timeout=self.timeout,
        )
        return parse_service_configuration(_response_json(response), resource_id=resource_id, service_id=service_id)

    def fetch_start_intervals(self, *, resource_id: str, service_id: str, date: str, timezone: str = DEFAULT_ANNY_TIMEZONE) -> list[AnnyTimeSlot]:
        return self._fetch_intervals("start", resource_id=resource_id, service_id=service_id, date_key="date", date_value=date, timezone=timezone)

    def fetch_end_intervals(self, *, resource_id: str, service_id: str, date_time: str, timezone: str = DEFAULT_ANNY_TIMEZONE) -> list[AnnyTimeSlot]:
        return self._fetch_intervals("end", resource_id=resource_id, service_id=service_id, date_key="date_time", date_value=date_time, timezone=timezone)

    def fetch_start_dates(
        self,
        *,
        resource_id: str,
        service_id: str,
        start_date: str,
        end_date: str,
        timezone: str = DEFAULT_ANNY_TIMEZONE,
    ) -> list[AnnyAvailabilityDate]:
        response = self.session.get(
            f"{ANNY_API_URL}/availability/start-dates",
            params=[
                ("start_date", start_date),
                ("end_date", end_date),
                (f"service_id[{service_id}]", "1"),
                ("resource_id", resource_id),
                ("timezone", timezone),
            ],
            timeout=self.timeout,
        )
        return [parse_availability_date(item) for item in as_list(_response_json(response))]

    def fetch_availability_periods(self, *, resource_id: str, start_date: str, end_date: str, timezone: str = DEFAULT_ANNY_TIMEZONE) -> list[AnnyAvailabilityPeriod]:
        response = self.session.get(
            f"{ANNY_API_URL}/availability/periods",
            params=[("r[]", resource_id), ("start_date", start_date), ("end_date", end_date), ("timezone", timezone)],
            timeout=self.timeout,
        )
        payload = _response_json(response)
        return [parse_availability_period(item, resource_id=resource_id) for item in as_list(payload.get(resource_id))]

    def fetch_calendar_events(self, *, resource_id: str, start_date: str, end_date: str, timezone: str = DEFAULT_ANNY_TIMEZONE) -> list[AnnyCalendarEvent]:
        response = self.session.get(
            f"{ANNY_API_URL}/calendar-events",
            params=[("start_date", start_date), ("end_date", end_date), ("resource_id[]", resource_id), ("timezone", timezone)],
            timeout=self.timeout,
        )
        payload = _response_json(response).get("data", {})
        return [parse_calendar_event(item) for item in as_list(payload.get("events"))]

    def calculate_booking_quote(self, *, resource_id: str, service_id: str, start_date: str, end_date: str) -> AnnyBookingQuote:
        payload = {
            "resource_id": resource_id,
            "service_id": {service_id: 1},
            "timeslot_series_id": None,
            "start_date": start_date,
            "end_date": end_date,
            "description": "",
            "customer_note": "",
            "add_ons_by_service": {service_id: [[]]},
            "sub_bookings_by_service": {},
            "strategy": "single-resource",
            "prevent_applying_default_quota": False,
        }
        response = self.session.post(
            f"{ANNY_API_URL}/order/bookings/calculate",
            params={"check_availability": "0"},
            json=payload,
            headers={"content-type": "application/vnd.api+json"},
            timeout=self.timeout,
        )
        return parse_booking_quote(_response_json(response), resource_id=resource_id, service_id=service_id)

    def _fetch_intervals(self, endpoint: str, *, resource_id: str, service_id: str, date_key: str, date_value: str, timezone: str) -> list[AnnyTimeSlot]:
        response = self.session.get(
            f"{ANNY_API_URL}/intervals/{endpoint}",
            params=[(date_key, date_value), ("resource_id", resource_id), (f"service_id[{service_id}]", "1"), ("timezone", timezone)],
            timeout=self.timeout,
        )
        return [parse_time_slot(item) for item in as_list(_response_json(response))]

    def _resource_scope_path(self) -> str:
        if self.customer_account_id:
            return f"customer-accounts/{self.customer_account_id}"
        return f"organizations/{self.organization_slug}"


def _bearer(token: str) -> str:
    token = token.strip()
    return token if token.lower().startswith("bearer ") else f"Bearer {token}"


def _response_json(response: Response):
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as error:
        content_type = response.headers.get("content-type", "unknown")
        raise requests.HTTPError(
            f"Anny returned a non-JSON response ({content_type}); member-only resources may require an auth_token.",
            response=response,
        ) from error
