from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_exam_registration_client import (  # noqa: E402
    inspect_exam_registration_support,
    prepare_exam_registration,
    register_for_exam,
)
from tue_api_wrapper.client import AlmaClient  # noqa: E402


OVERVIEW_HTML = """
<form id="detailViewData" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e1s4" enctype="multipart/form-data">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="detailViewData_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e1s4" />
  <a
    id="detailViewData:tabContainer:term-planning-container:courseGroupsTable:courseGroupsTableTable:37:showDetailsViewForLinkedExamination"
    onclick="mojarra.jsfcljs(document.getElementById('detailViewData'),{'linkedExamUnitId':'63233'},'')"
  >Pruefungsdetails</a>
</form>
"""

COURSE_DETAIL_HTML = """
<form id="detailViewData" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e6s2" enctype="multipart/form-data">
  <input type="hidden" name="detailViewData_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e6s2" />
  <button name="detailViewData:tabContainer:term-planning-container:tabs:linkedExaminationsTab">Pruefungen</button>
</form>
"""

LINKED_EXAMS_HTML = """
<form id="detailViewData" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e6s3" enctype="multipart/form-data">
  <input type="hidden" name="detailViewData_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e6s3" />
  <a
    id="detailViewData:tabContainer:term-planning-container:courseGroupsTable:courseGroupsTableTable:29:showDetailsViewForLinkedExamination"
    onclick="mojarra.jsfcljs(document.getElementById('detailViewData'),{'linkedExamUnitId':'63120'},'')"
  >Pruefungsdetails</a>
</form>
"""

DETAIL_HTML = """
<form id="detailViewData" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e1s6" enctype="multipart/form-data">
  <input type="hidden" name="detailViewData_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e1s6" />
  <input type="hidden" name="unitId" value="63233" />
  <input type="hidden" name="periodUsageId" value="" />
  <input type="hidden" name="planelementId" value="" />
  <button name="detailViewData:tabContainer:term-planning-container:examinationPeriod_1:parallelGroupSchedule_2:appointmentsFieldset:buttons:anmelden">
    anmelden
  </button>
</form>
<div>INFO-THEO-1-9CP: Probabilistic Machine Learning Leistung wird verwendet fuer:</div>
"""

INSTRUCTION_HTML = """
<form id="enrollForm" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e1s8">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="checkbox" name="enrollForm:instructions:confirmInstruction" value="true" />
  <button name="enrollForm:instructions:enrollAccept" value="Weiter">Weiter</button>
  <input type="hidden" name="enrollForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e1s8" />
</form>
"""

CONFIRM_HTML = """
<form id="enrollForm" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e1s9">
  <input type="hidden" name="enrollForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e1s9" />
  <input type="hidden" name="planelementId" value="" />
  <table>
    <tr><td>Pruefungsperiode 1</td><td>
      <button
        name="enrollForm:recordList:unit-Belegung:unit-BelegungTable:0:anEchtzeit"
        onclick="mojarra.jsfcljs(document.getElementById('enrollForm'),{'planelementId':'723548'},'')"
      >anmelden</button>
    </td></tr>
  </table>
</form>
"""

FINAL_HTML = """
<form id="enrollSuccessForm">
  <div class="messages-infobox-scroll-container">Bestaetigung: Eine Aenderung fuer Probabilistic Machine Learning</div>
  <p>Nicht angemeldet</p>
</form>
"""


class _FakeResponse:
    def __init__(self, *, url: str, text: str) -> None:
        self.url = url
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _RecordingSession:
    def __init__(self, *, get_text: str, post_responses: list[_FakeResponse]) -> None:
        self.headers: dict[str, str] = {}
        self.posts: list[dict[str, object]] = []
        self.get_text = get_text
        self._post_responses = list(post_responses)

    def get(self, url: str, timeout: int, allow_redirects: bool = True) -> _FakeResponse:
        return _FakeResponse(url=url, text=self.get_text)

    def post(
        self,
        url: str,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[None, str]] | None = None,
        timeout: int = 30,
        allow_redirects: bool = True,
    ) -> _FakeResponse:
        payload = dict(data or {})
        if files is not None:
            payload = {name: value for name, (_, value) in files.items()}
        self.posts.append({"url": url, "data": payload, "used_files": files is not None})
        if not self._post_responses:
            raise AssertionError(f"No fake POST response left for {url}")
        return self._post_responses.pop(0)


class AlmaExamRegistrationTests(unittest.TestCase):
    def test_prepare_exam_registration_accepts_instruction_step(self) -> None:
        session = _RecordingSession(
            get_text=OVERVIEW_HTML,
            post_responses=[
                _FakeResponse(url="https://alma.example/detail", text=DETAIL_HTML),
                _FakeResponse(url="https://alma.example/instructions", text=INSTRUCTION_HTML),
                _FakeResponse(url="https://alma.example/options", text=CONFIRM_HTML),
            ],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        options = prepare_exam_registration(client, exam_unit_id="63233")

        self.assertTrue(options.requires_instruction_accept)
        self.assertEqual(options.exam_unit_id, "63233")
        self.assertEqual(options.options[0].planelement_id, "723548")
        self.assertEqual(session.posts[0]["data"]["linkedExamUnitId"], "63233")
        self.assertEqual(session.posts[1]["data"]["belegungsAktion"], "ANMELDUNG")
        self.assertEqual(session.posts[2]["data"]["enrollForm:instructions:confirmInstruction"], "true")

    def test_register_for_exam_can_open_linked_exams_tab_and_confirm_directly(self) -> None:
        session = _RecordingSession(
            get_text=COURSE_DETAIL_HTML,
            post_responses=[
                _FakeResponse(url="https://alma.example/linked", text=LINKED_EXAMS_HTML),
                _FakeResponse(url="https://alma.example/detail", text=DETAIL_HTML.replace("63233", "63120")),
                _FakeResponse(url="https://alma.example/options", text=CONFIRM_HTML.replace("723548", "722795")),
                _FakeResponse(url="https://alma.example/done", text=FINAL_HTML),
            ],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        result = register_for_exam(client, "https://alma.example/alma/pages/plan/individualTimetable.xhtml", exam_unit_id="63120")

        self.assertEqual(result.status, "registered")
        self.assertEqual(result.selected_option.planelement_id, "722795")
        self.assertIn("linkedExaminationsTab", session.posts[0]["data"]["detailViewData:_idcl"])
        self.assertEqual(session.posts[1]["data"]["linkedExamUnitId"], "63120")
        self.assertEqual(session.posts[3]["data"]["planelementId"], "722795")

    def test_inspect_exam_registration_reports_support(self) -> None:
        session = _RecordingSession(get_text=DETAIL_HTML, post_responses=[])
        client = AlmaClient(base_url="https://alma.example", session=session)

        support = inspect_exam_registration_support(client, "https://alma.example/alma/pages/plan/individualTimetable.xhtml")

        self.assertTrue(support.supported)
        self.assertEqual(support.action, "ANMELDUNG")
        self.assertEqual(support.number, "INFO-THEO-1-9CP")


if __name__ == "__main__":
    unittest.main()
