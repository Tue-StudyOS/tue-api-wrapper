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
        self.assertEqual(page.entries[0].category, "Veranstaltung")
        self.assertEqual(page.entries[0].number, "GTCNEURO")
        self.assertEqual(page.entries[0].event_type, "Vorlesung/Übung")
        self.assertEqual(page.entries[0].status, "storniert")
        self.assertEqual(page.entries[0].semester, "SoSe 2026")
        self.assertIn("jeden Mittwoch", page.entries[0].schedule_text)
        self.assertNotIn("Details anzeigen", page.entries[0].schedule_text)
        self.assertNotIn("Informationen zu Belegzeiträumen", page.entries[0].schedule_text)
        self.assertTrue(page.entries[0].detail_url.endswith("unitId=42&periodId=229"))

    def test_parse_enrollment_page_extracts_exam_rows(self) -> None:
        html = """
        <form id="studentOverviewForm">
          <select name="studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input">
            <option value="229" selected="selected">Sommersemester 2026</option>
          </select>
          <h2>Prüfung: INFO-THEO-1-9CP THEO</h2>
          <table>
            <tr>
              <td>Termine und Räume Status Aktionen</td>
              <td>1. Parallelgruppe Probabilistic Machine Learning Donnerstag 23.07.26 Keine Uhrzeit festgelegt Prüfungsform: Schriftlich oder mündlich Prüfer/-in: Prof. Dr. Macke</td>
              <td>Ihr aktueller Status: zugelassen Semester der Leistung: SoSe 2026 Versuch (gilt nur für Prüfungen): 1</td>
              <td><a href="/alma/pages/startFlow.xhtml?_flowId=detailView-flow&amp;unitId=63233">Details anzeigen</a></td>
            </tr>
          </table>
        </form>
        """

        page = parse_enrollment_page(html)

        self.assertEqual(page.entries[0].category, "Prüfung")
        self.assertEqual(page.entries[0].event_type, "Prüfung")
        self.assertEqual(page.entries[0].number, "INFO-THEO-1-9CP")
        self.assertEqual(page.entries[0].title, "Probabilistic Machine Learning")
        self.assertEqual(page.entries[0].status, "zugelassen")
        self.assertEqual(page.entries[0].semester, "SoSe 2026")
        self.assertEqual(page.entries[0].attempt, "1")
        self.assertIn("Donnerstag 23.07.26", page.entries[0].schedule_text)
        self.assertIn("Prüfungsform: Schriftlich oder mündlich", page.entries[0].schedule_text)


if __name__ == "__main__":
    unittest.main()
