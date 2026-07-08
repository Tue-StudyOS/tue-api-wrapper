from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_timetable_html import parse_timetable_contract
from tue_api_wrapper.config import AlmaServiceUnavailableError
from tue_api_wrapper.html_contract import extract_login_form

MAINTENANCE_HTML = """
<html>
  <body>
    <main>
      <h1>Alma</h1>
      <p>Wartung bis voraussichtlich 17 Uhr</p>
    </main>
  </body>
</html>
"""


class AlmaAvailabilityTests(unittest.TestCase):
    def test_login_form_reports_alma_maintenance_page(self) -> None:
        with self.assertRaisesRegex(
            AlmaServiceUnavailableError,
            "Alma is currently unavailable for maintenance: Wartung bis voraussichtlich 17 Uhr.",
        ):
            extract_login_form(
                html=MAINTENANCE_HTML,
                page_url="https://alma.uni-tuebingen.de/alma/pages/cs/sys/portal/hisinoneStartPage.faces",
            )

    def test_timetable_contract_reports_alma_maintenance_page(self) -> None:
        with self.assertRaisesRegex(
            AlmaServiceUnavailableError,
            "Alma is currently unavailable for maintenance: Wartung bis voraussichtlich 17 Uhr.",
        ):
            parse_timetable_contract(
                MAINTENANCE_HTML,
                "https://alma.uni-tuebingen.de/alma/pages/plan/individualTimetable.xhtml",
            )


if __name__ == "__main__":
    unittest.main()
