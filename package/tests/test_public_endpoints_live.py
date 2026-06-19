from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.campus_client import CampusClient
from tue_api_wrapper.event_calendar_client import EventCalendarClient
from tue_api_wrapper.praxisportal_client import PraxisportalClient
from tue_api_wrapper.seatfinder_client import SeatfinderClient
from tue_api_wrapper.talks_client import TalksClient
from tue_api_wrapper.timms_client import TimmsClient


LIVE_PUBLIC_TESTS_ENABLED = os.environ.get("TUE_API_LIVE_PUBLIC_TESTS") == "1"


@unittest.skipUnless(LIVE_PUBLIC_TESTS_ENABLED, "set TUE_API_LIVE_PUBLIC_TESTS=1 to run live public endpoint tests")
class LivePublicEndpointTests(unittest.TestCase):
    def test_seatfinder_public_endpoint_returns_known_location(self) -> None:
        availability = _retry(lambda: SeatfinderClient(timeout=15).fetch_availability(locations=("UBH1",)))

        self.assertEqual(len(availability.locations), 1)
        location = availability.locations[0]
        self.assertEqual(location.location_id, "UBH1")
        self.assertGreater(location.total_seats or 0, 0)
        self.assertTrue(availability.source_url.startswith("https://seatfinder.bibliothek.kit.edu/tuebingen/"))

    def test_timms_public_tree_and_suggestions_are_available(self) -> None:
        client = TimmsClient(timeout=15)

        tree = _retry(lambda: client.fetch_tree())
        suggestions = _retry(lambda: client.suggest("Informatik", limit=3))

        self.assertTrue(tree.source_url.startswith("https://timms.uni-tuebingen.de/"))
        self.assertTrue(any(node.label == "Universität Tübingen" for node in tree.nodes))
        self.assertIn("informatik", [suggestion.lower() for suggestion in suggestions])

    def test_campus_public_canteen_endpoint_returns_wilhelmstrasse(self) -> None:
        canteen = _retry(lambda: CampusClient(timeout=15).fetch_canteen(611))

        self.assertEqual(canteen.canteen_id, "611")
        self.assertIn("Wilhelmstraße", canteen.canteen)
        self.assertEqual(canteen.page_url, "https://www.my-stuwe.de/mensa/mensa-wilhelmstrasse-tuebingen/")

    def test_university_events_public_feed_is_parseable(self) -> None:
        events = _retry(lambda: EventCalendarClient(timeout=15).fetch_events(limit=3))

        self.assertEqual(events.feed_url, "https://uni-tuebingen.de/universitaet/campusleben/veranstaltungen/veranstaltungskalender/feed.xml")
        self.assertLessEqual(events.returned_hits, 3)
        self.assertGreaterEqual(events.total_hits, events.returned_hits)
        if events.items:
            self.assertTrue(events.items[0].title)
            self.assertTrue(events.items[0].starts_at)

    def test_talks_public_previous_endpoint_returns_items(self) -> None:
        talks = _retry(lambda: TalksClient(timeout=15).fetch_talks(scope="previous", limit=3))

        self.assertEqual(talks.source_url, "https://talks.tuebingen.ai/talks")
        self.assertGreaterEqual(talks.returned_hits, 1)
        self.assertLessEqual(talks.returned_hits, 3)
        self.assertTrue(talks.items[0].title)

    def test_praxisportal_public_search_returns_current_projects(self) -> None:
        response = _retry(lambda: PraxisportalClient(timeout=15).search_projects(per_page=3, sort="newest"))

        self.assertEqual(response.source_url, "https://www.praxisportal.uni-tuebingen.de/candidate/search")
        self.assertGreaterEqual(response.total_hits, len(response.items))
        self.assertLessEqual(len(response.items), 3)
        self.assertTrue(response.items[0].title)
        self.assertGreaterEqual(len(response.filters.project_types), 1)


def _retry(call):
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            return call()
        except Exception as error:
            last_error = error
            if attempt == 0:
                time.sleep(1)
    assert last_error is not None
    raise last_error


if __name__ == "__main__":
    unittest.main()
