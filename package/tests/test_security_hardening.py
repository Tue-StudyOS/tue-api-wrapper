from __future__ import annotations

import os
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_partial import extract_partial_updates
from tue_api_wrapper.alma_portal_messages_html import parse_portal_messages_settings
from tue_api_wrapper.alma_portal_messages_items_html import parse_portal_messages_partial_response
from tue_api_wrapper import api_server
from tue_api_wrapper.config import AlmaParseError
from tue_api_wrapper.event_calendar_client import parse_university_events_feed
from tue_api_wrapper.fitness_client import parse_kuf_training_count_image


ENTITY_PARTIAL_RESPONSE = """<!DOCTYPE partial-response [
<!ENTITY payload "expanded-content">
]>
<partial-response><changes><update id="content">&payload;</update></changes></partial-response>
"""

ENTITY_EVENT_FEED = """<!DOCTYPE rss [
<!ENTITY payload "expanded-title">
]>
<rss><channel><link>https://example.test</link><item><title>&payload;</title></item></channel></rss>
"""


class SecurityHardeningTests(unittest.TestCase):
    def test_alma_xml_parsers_reject_entity_declarations(self) -> None:
        parsers = (
            lambda: extract_partial_updates(ENTITY_PARTIAL_RESPONSE),
            lambda: parse_portal_messages_settings(ENTITY_PARTIAL_RESPONSE, "https://alma.example/start"),
            lambda: parse_portal_messages_partial_response(ENTITY_PARTIAL_RESPONSE, "https://alma.example/start"),
        )

        for parser in parsers:
            with self.subTest(parser=parser), self.assertRaises(AlmaParseError):
                parser()

    def test_event_feed_parser_rejects_entity_declarations(self) -> None:
        with self.assertRaisesRegex(ValueError, "not valid XML"):
            parse_university_events_feed(ENTITY_EVENT_FEED)

    def test_oversized_fitness_image_is_rejected_before_decode(self) -> None:
        image = MagicMock()
        image.__enter__.return_value = image
        image.width = 401
        image.height = 1

        with patch("tue_api_wrapper.fitness_client.Image.open", return_value=image):
            with self.assertRaisesRegex(ValueError, "larger than expected"):
                parse_kuf_training_count_image(b"image header")

        image.convert.assert_not_called()

    def test_api_server_defaults_to_loopback(self) -> None:
        with patch.dict(os.environ, {"PORT": "8123"}, clear=True), patch.object(api_server.uvicorn, "run") as run:
            api_server.main()

        run.assert_called_once_with(
            "tue_api_wrapper.api_server:app",
            host="127.0.0.1",
            port=8123,
            reload=False,
        )


if __name__ == "__main__":
    unittest.main()
