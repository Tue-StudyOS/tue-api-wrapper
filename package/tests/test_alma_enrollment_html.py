from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_academics_html import parse_enrollment_page


class AlmaEnrollmentHtmlTests(unittest.TestCase):
    def test_parse_enrollment_page_extracts_course_rows(self) -> None:
        html = """
        <form id="studentOverviewForm">
          <select name="studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input">
            <option value="229" selected="selected">Sommersemester 2026</option>
          </select>
          <h2>Veranstaltung: Vorlesung/Übung GTCNEURO Neural Data Science</h2>
          <table>
            <tr>
              <td>
                <div>1. Parallelgruppe Neural Data Science</div>
                <div>jeden Mittwoch (15.04.26 bis 22.07.26) von 10:15 bis 11:45 wöchentlich</div>
                <div>Status Aktionen Details anzeigen Informationen zu Belegzeiträumen</div>
                <a href="/alma/pages/cm/exa/searchRoomDetail.xhtml?roomId=471">Raumdetails für Hörsaal A2 anzeigen</a>
              </td>
              <td>
                <div>Status</div>
                <div>Ihr aktueller Status: storniert</div>
                <div>Semester der Leistung: SoSe 2026</div>
              </td>
              <td>
                <a href="/alma/pages/startFlow.xhtml?_flowId=detailView-flow&amp;unitId=42&amp;periodId=229">Details anzeigen</a>
              </td>
            </tr>
          </table>
        </form>
        """

        page = parse_enrollment_page(html)

        self.assertEqual(page.entries[0].title, "Neural Data Science")
        self.assertEqual(page.entries[0].number, "GTCNEURO")
        self.assertEqual(page.entries[0].event_type, "Vorlesung/Übung")
        self.assertEqual(page.entries[0].status, "storniert")
        self.assertEqual(page.entries[0].semester, "SoSe 2026")
        self.assertIn("jeden Mittwoch", page.entries[0].schedule_text)
        self.assertNotIn("Details anzeigen", page.entries[0].schedule_text)
        self.assertNotIn("Informationen zu Belegzeiträumen", page.entries[0].schedule_text)
        self.assertTrue(page.entries[0].detail_url.endswith("unitId=42&periodId=229"))


if __name__ == "__main__":
    unittest.main()
