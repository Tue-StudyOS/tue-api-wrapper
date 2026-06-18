from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.client import AlmaClient  # noqa: E402


ENROLLMENT_HTML = """
<form id="studentOverviewForm" action="/alma/pages/cm/exa/enrollment/info/start.xhtml?_flowExecutionKey=e13s1" enctype="multipart/form-data">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="studentOverviewForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e13s1" />
  <select name="studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input">
    <option value="2025.2.2">Wintersemester 2025/26</option>
    <option value="2026.2.1" selected="selected">Sommersemester 2026</option>
  </select>
  <button name="studentOverviewForm:enrollmentsDiv:termSelector:refresh">Refresh</button>
  <button name="studentOverviewForm:enrollmentsDiv:infoBoxDiv:enrollStudentListJobConfigurationButtons:jobConfigurationButtons:0:job2">Belegungen</button>
  <div id="studentOverviewForm:enrollmentsDiv:termEnrollmentDiv">
    <h2>Veranstaltung: Vorlesung/Übung GTCNEURO Neural Data Science</h2>
    <table><tr><td>jeden Mittwoch Status Aktionen</td><td>Ihr aktueller Status: zugelassen Semester der Leistung: SoSe 2026</td></tr></table>
  </div>
</form>
"""

TERM_PARTIAL = """
<?xml version="1.0" encoding="UTF-8"?>
<partial-response><changes>
  <update id="studentOverviewForm:enrollmentsDiv:termEnrollmentDiv"><![CDATA[
    <div id="studentOverviewForm:enrollmentsDiv:termEnrollmentDiv">
      <h2>Veranstaltung: Seminar ML5401 Statistical Machine Learning</h2>
      <table><tr><td>Blocktermin Status Aktionen</td><td>Ihr aktueller Status: angemeldet Semester der Leistung: WiSe 2025/26</td></tr></table>
    </div>
  ]]></update>
  <update id="j_id__v_20:javax.faces.ViewState:1"><![CDATA[e13s1]]></update>
</changes></partial-response>
"""

REPORT_PARTIAL = """
<?xml version="1.0" encoding="UTF-8"?>
<partial-response><changes>
  <update id="studentOverviewForm:enrollmentsDiv:infoBoxDiv:enrollStudentListJobConfigurationButtons:jobDownload"><![CDATA[
    <div id="studentOverviewForm:enrollmentsDiv:infoBoxDiv:enrollStudentListJobConfigurationButtons:jobDownload">
      <a class="downloadFile noDisplay" href="/alma/rds?state=docdownload&amp;docId=belegungen-1" target="_blank">download</a>
    </div>
  ]]></update>
  <update id="j_id__v_20:javax.faces.ViewState:1"><![CDATA[e13s1]]></update>
</changes></partial-response>
"""


class _FakeResponse:
    def __init__(
        self,
        *,
        url: str,
        text: str = "",
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.text = text
        self.content = content if content is not None else text.encode()
        self.headers = headers or {"content-type": "text/html; charset=utf-8"}

    def raise_for_status(self) -> None:
        return None


class _Session:
    def __init__(self, *, gets: list[_FakeResponse], posts: list[_FakeResponse]) -> None:
        self.headers: dict[str, str] = {}
        self.gets = list(gets)
        self.post_responses = list(posts)
        self.posts: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, timeout: int, allow_redirects: bool = True) -> _FakeResponse:
        if not self.gets:
            raise AssertionError(f"No fake GET response left for {url}")
        return self.gets.pop(0)

    def post(self, url: str, data: dict[str, str], timeout: int, allow_redirects: bool = True) -> _FakeResponse:
        self.posts.append((url, dict(data)))
        if not self.post_responses:
            raise AssertionError(f"No fake POST response left for {url}")
        return self.post_responses.pop(0)


class AlmaEnrollmentClientTests(unittest.TestCase):
    def test_fetch_enrollment_page_switches_term_from_partial_response(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://alma.example/enrollments", text=ENROLLMENT_HTML)],
            posts=[_FakeResponse(url="https://alma.example/enrollments", text=TERM_PARTIAL)],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        page = client.fetch_enrollment_page(term="Wintersemester 2025/26")

        self.assertEqual(page.selected_term, "Wintersemester 2025/26")
        self.assertEqual(page.entries[0].title, "Statistical Machine Learning")
        self.assertEqual(page.entries[0].number, "ML5401")
        payload = session.posts[0][1]
        self.assertEqual(payload["studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input"], "2025.2.2")
        self.assertEqual(payload["activePageElementId"], "studentOverviewForm:enrollmentsDiv:termSelector:refresh")

    def test_download_enrollment_report_uses_generated_docdownload_link(self) -> None:
        session = _Session(
            gets=[
                _FakeResponse(url="https://alma.example/enrollments", text=ENROLLMENT_HTML),
                _FakeResponse(url="https://alma.example/enrollments", text=ENROLLMENT_HTML),
                _FakeResponse(
                    url="https://alma.example/alma/rds?state=docdownload&docId=belegungen-1",
                    content=b"%PDF-enrollments",
                    headers={"content-type": "application/pdf"},
                ),
            ],
            posts=[_FakeResponse(url="https://alma.example/enrollments", text=REPORT_PARTIAL)],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        reports = client.list_enrollment_reports()
        document = client.download_enrollment_report(trigger_name=reports[0].trigger_name)

        self.assertEqual(reports[0].label, "Belegungen")
        self.assertEqual(document.data, b"%PDF-enrollments")
        self.assertEqual(session.posts[0][1]["activePageElementId"], reports[0].trigger_name)


if __name__ == "__main__":
    unittest.main()
