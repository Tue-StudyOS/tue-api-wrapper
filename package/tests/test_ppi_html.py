from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.ppi_html import parse_borrowed_lectures, parse_lecture_catalog


LECTURES_HTML = """
<html><body>
  <nav><a>Anzahl Tokens: 2</a></nav>
  <table id="table">
    <tr><th>Vorlesungstitel</th><th>Protokolle</th><th>Ausleihen</th></tr>
    <tr>
      <td>Natural Language Processing</td><td>7</td>
      <td><a href="download.php"><img src="static/img/protocolCheckmark.png">Ausgeliehen</a></td>
    </tr>
    <tr>
      <td>Machine Learning</td><td>4</td>
      <td><a href="?borrow=42"><img src="static/img/protocol.png">Ausleihen</a></td>
    </tr>
    <tr>
      <td>Unavailable Course</td><td>0</td>
      <td><a href=""><img src="static/img/protocolNotAvailable.png">Keine Protokolle</a></td>
    </tr>
  </table>
</body></html>
"""


BORROWED_HTML = """
<html><body>
  <nav><a>Number of Tokens: 2</a></nav>
  <table id="table">
    <tr><th>Lecture</th><th>Borrowed until</th><th>Download</th><th>Report</th></tr>
    <tr>
      <td>Natural Language Processing</td><td>19.08.2026 12:00</td>
      <td><a href="?lecture=17"><img src="static/img/protocolDownload.png">Download</a></td>
      <td><a href="?report=17">Report</a></td>
    </tr>
  </table>
</body></html>
"""


class PpiHtmlTests(unittest.TestCase):
    def test_parse_lecture_catalog_preserves_server_states(self) -> None:
        catalog = parse_lecture_catalog(LECTURES_HTML, "https://ppi.example/lectures.php")

        self.assertEqual(catalog.tokens, 2)
        self.assertEqual(len(catalog.lectures), 3)
        borrowed, borrowable, unavailable = catalog.lectures
        self.assertTrue(borrowed.borrowed)
        self.assertIsNone(borrowed.id)
        self.assertEqual(borrowable.id, 42)
        self.assertTrue(borrowable.can_borrow)
        self.assertFalse(unavailable.can_borrow)

    def test_parse_borrowed_lectures_extracts_download_entitlement(self) -> None:
        page = parse_borrowed_lectures(BORROWED_HTML, "https://ppi.example/download.php")

        self.assertEqual(page.tokens, 2)
        self.assertEqual(len(page.lectures), 1)
        lecture = page.lectures[0]
        self.assertEqual(lecture.id, 17)
        self.assertEqual(lecture.title, "Natural Language Processing")
        self.assertEqual(lecture.borrowed_until, "19.08.2026 12:00")
        self.assertTrue(lecture.download_available)


if __name__ == "__main__":
    unittest.main()
