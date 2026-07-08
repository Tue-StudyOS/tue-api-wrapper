from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper import api_routes_moodle
from tue_api_wrapper.config import AlmaParseError, AlmaServiceUnavailableError


class APIErrorTranslationTests(unittest.TestCase):
    def test_missing_backend_credentials_are_service_unavailable(self) -> None:
        error = AlmaParseError(
            "Set UNI_USERNAME and UNI_PASSWORD before using authenticated Moodle endpoints. "
            "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
        )

        response = api_routes_moodle._translate_error(error)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.detail, str(error))

    def test_alma_maintenance_is_service_unavailable(self) -> None:
        error = AlmaServiceUnavailableError(
            "Alma is currently unavailable for maintenance: Wartung bis voraussichtlich 17 Uhr."
        )

        response = api_routes_moodle._translate_error(error)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.detail, str(error))

    def test_other_backend_parse_errors_remain_bad_request(self) -> None:
        response = api_routes_moodle._translate_error(AlmaParseError("A non-empty course title is required."))

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
