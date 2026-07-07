from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.anny_client import AnnyClient
from tue_api_wrapper.anny_parsing import parse_resource_page
from tue_api_wrapper.sdk import TuebingenPublicClient
from tue_api_wrapper.sdk.public import PublicAnnyApi


RESOURCE_PAGE_PAYLOAD = {
    "meta": {"page": {"current-page": 1, "total": 1, "last-page": 1}},
    "data": [
        {
            "type": "resources",
            "id": "112141",
            "attributes": {
                "slug": "raum-525-qopm2e4dhw",
                "name": "Room 525: Ammerbau, 5th Floor",
                "plain_description": "Group work room.",
                "timezone": "Europe/Berlin",
                "quantity": 1,
                "bookings_enabled": True,
                "booking_requires_community": True,
                "viewing_requires_community": True,
            },
            "relationships": {
                "category": {"data": {"type": "resource-categories", "id": "596"}},
                "cover_image": {"data": {"type": "images", "id": "116747"}},
                "location": {
                    "data": {
                        "type": "addresses",
                        "id": "41117",
                        "meta": {"address_line": "Wilhelmstrasse 32, 72074 Tübingen, DE"},
                    }
                },
                "services": {
                    "data": [
                        {
                            "type": "services",
                            "id": "7880",
                            "meta": {
                                "duration_preview": "From 1 to 2 hours",
                                "supports_instant_booking": True,
                            },
                        }
                    ]
                },
                "resource_properties": {"data": [{"type": "resource-properties", "id": "262816"}]},
            },
        }
    ],
    "included": [
        {"type": "resource-categories", "id": "596", "attributes": {"name": "Group Space"}},
        {"type": "images", "id": "116747", "attributes": {"medium_path": "https://cdn.anny.eu/image.jpg"}},
        {"type": "addresses", "id": "41117", "attributes": {"name": "Universitätsbibliothek Tübingen"}},
        {
            "type": "services",
            "id": "7880",
            "attributes": {
                "name": "Max. 2h/day, max. 4h/week",
                "slug": "neue-buchungsoption-apour1itvy5nbgjl",
                "min_duration": 60,
                "max_duration": 120,
                "booking_interval": 60,
            },
        },
        {
            "type": "resource-properties",
            "id": "262816",
            "attributes": {"value": 10},
            "relationships": {"property": {"data": {"type": "properties", "id": "5"}}},
        },
        {"type": "properties", "id": "5", "attributes": {"label": "Capacity", "private": False}},
    ],
}


class AnnyClientTests(unittest.TestCase):
    def test_parse_resource_page_maps_har_json_api_shape(self) -> None:
        page = parse_resource_page(RESOURCE_PAGE_PAYLOAD, source_url="https://b.anny.eu/resources")

        room = page.items[0]
        self.assertEqual(page.total_results, 1)
        self.assertEqual(room.slug, "raum-525-qopm2e4dhw")
        self.assertEqual(room.category, "Group Space")
        self.assertEqual(room.location, "Wilhelmstrasse 32, 72074 Tübingen, DE")
        self.assertEqual(room.image_url, "https://cdn.anny.eu/image.jpg")
        self.assertTrue(room.booking_requires_community)
        self.assertEqual(room.services[0].id, "7880")
        self.assertEqual(room.services[0].duration_label, "From 1 to 2 hours")
        self.assertEqual(room.services[0].max_duration, 120)
        self.assertEqual(room.properties[0].label, "Capacity")
        self.assertEqual(room.properties[0].value, 10)

    def test_resource_listing_defaults_to_public_organization_scope(self) -> None:
        session = _RecordingSession(get_responses=[_FakeResponse(RESOURCE_PAGE_PAYLOAD)])
        client = AnnyClient(session=session)

        client.list_resources(page_size=5)

        self.assertIn("/organizations/universitaetsbibliothek-tuebingen/all-resources", session.gets[0]["url"])
        self.assertIn(("page[size]", 5), session.gets[0]["params"])
        self.assertEqual(session.headers["x-app-key"], "anny_shop")

    def test_resource_listing_can_use_explicit_customer_account_scope(self) -> None:
        session = _RecordingSession(get_responses=[_FakeResponse(RESOURCE_PAGE_PAYLOAD)])
        client = AnnyClient(session=session, customer_account_id="customer-123")

        client.list_resources()

        self.assertIn("/customer-accounts/customer-123/all-resources", session.gets[0]["url"])

    def test_client_accepts_explicit_bearer_token_for_member_context(self) -> None:
        session = _RecordingSession(get_responses=[_FakeResponse(RESOURCE_PAGE_PAYLOAD)])

        AnnyClient(session=session, auth_token="test-token")

        self.assertEqual(session.headers["authorization"], "Bearer test-token")

    def test_intervals_and_quote_match_har_contract(self) -> None:
        interval_payload = [
            {
                "start_date": "2026-07-08T19:00:00+02:00",
                "end_date": "2026-07-08T20:00:00+02:00",
                "unit": "minute",
                "available": True,
                "quota": 1,
                "remaining_number_available": 1,
                "messages": [],
            }
        ]
        quote_payload = {
            "start_date": "2026-07-08T17:00:00+00:00",
            "end_date": "2026-07-08T18:00:00+00:00",
            "charged_duration": 60,
            "total": 0,
            "currency": "EUR",
            "price_hidden": True,
            "items": [{"title": "Room 525: 08/07/2026 19:00 - 20:00"}],
        }
        session = _RecordingSession(
            get_responses=[_FakeResponse(interval_payload)],
            post_responses=[_FakeResponse(quote_payload)],
        )
        client = AnnyClient(session=session)

        slots = client.fetch_start_intervals(resource_id="112141", service_id="7880", date="2026-07-08")
        quote = client.calculate_booking_quote(
            resource_id="112141",
            service_id="7880",
            start_date="2026-07-08T19:00:00+02:00",
            end_date="2026-07-08T20:00:00+02:00",
        )

        self.assertTrue(slots[0].available)
        self.assertIn(("service_id[7880]", "1"), session.gets[0]["params"])
        self.assertEqual(session.posts[0]["json"]["service_id"], {"7880": 1})
        self.assertEqual(session.posts[0]["json"]["add_ons_by_service"], {"7880": [[]]})
        self.assertEqual(session.posts[0]["params"], {"check_availability": "0"})
        self.assertEqual(session.posts[0]["headers"], {"content-type": "application/vnd.api+json"})
        self.assertEqual(quote.items, ["Room 525: 08/07/2026 19:00 - 20:00"])

    def test_non_json_anny_response_reports_member_context(self) -> None:
        session = _RecordingSession(
            post_responses=[
                _FakeResponse(
                    "<html>Forbidden</html>",
                    headers={"content-type": "text/html"},
                    json_error=ValueError("not json"),
                )
            ]
        )
        client = AnnyClient(session=session)

        with self.assertRaisesRegex(Exception, "member-only resources may require an auth_token"):
            client.calculate_booking_quote(
                resource_id="112141",
                service_id="7880",
                start_date="2026-07-08T19:00:00+02:00",
                end_date="2026-07-08T20:00:00+02:00",
            )

    def test_public_sdk_exposes_anny_facade(self) -> None:
        client = TuebingenPublicClient(anny=PublicAnnyApi(client=_FakeAnnyClient()))

        self.assertEqual(client.anny.resources(query="cube"), {"query": "cube"})
        self.assertEqual(client.anny.start_intervals(resource_id="112141", service_id="7880", date="2026-07-08"), ["slot"])


class _FakeResponse:
    def __init__(
        self,
        payload: object,
        *,
        url: str = "https://b.anny.eu/test",
        headers: dict[str, str] | None = None,
        json_error: Exception | None = None,
    ) -> None:
        self._payload = payload
        self.url = url
        self.headers = headers or {"content-type": "application/json"}
        self._json_error = json_error

    def json(self) -> object:
        if self._json_error:
            raise self._json_error
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _RecordingSession:
    def __init__(self, *, get_responses: list[_FakeResponse] | None = None, post_responses: list[_FakeResponse] | None = None) -> None:
        self.headers: dict[str, str] = {}
        self.get_responses = get_responses or []
        self.post_responses = post_responses or []
        self.gets: list[dict[str, object]] = []
        self.posts: list[dict[str, object]] = []

    def get(self, url: str, *, params: object = None, timeout: int = 0) -> _FakeResponse:
        self.gets.append({"url": url, "params": params, "timeout": timeout})
        return self.get_responses.pop(0)

    def post(
        self,
        url: str,
        *,
        params: object = None,
        json: object = None,
        headers: object = None,
        timeout: int = 0,
    ) -> _FakeResponse:
        self.posts.append({"url": url, "params": params, "json": json, "headers": headers, "timeout": timeout})
        return self.post_responses.pop(0)


class _FakeAnnyClient:
    def list_resources(self, *, query: str = "", page: int = 1, page_size: int = 25):
        return {"query": query}

    def fetch_start_intervals(self, *, resource_id: str, service_id: str, date: str, timezone: str = "Europe/Berlin"):
        return ["slot"]


if __name__ == "__main__":
    unittest.main()
