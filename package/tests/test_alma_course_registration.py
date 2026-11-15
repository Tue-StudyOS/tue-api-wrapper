from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_course_registration_client import (
    inspect_course_registration_support,
    prepare_course_registration,
    register_for_course,
)
from tue_api_wrapper.client import AlmaClient
from tue_api_wrapper.config import AlmaParseError


DETAIL_HTML = """
<form id="detailViewData" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e1s13" enctype="multipart/form-data">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="authenticity_token" value="token-1" />
  <select name="detailViewData:tabContainer:term-selection-container:termPeriodDropDownList_input">
    <option value="229" selected="selected">Sommer 2026</option>
  </select>
  <input name="detailViewData:tabContainer:term-planning-container:modules:moduleAssignments:moduleAssignmentsNavi2NumRowsInput" value="10" />
  <input name="detailViewData:tabContainer:term-planning-container:courseOfStudies:courseOfStudyAssignments:courseOfStudyAssignmentsNavi2NumRowsInput" value="10" />
  <input type="hidden" name="detailViewData_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e1s13" />
  <a
    id="detailViewData:tabContainer:further-functions-container:anmelden"
    onclick="mojarra.jsfcljs(document.getElementById('detailViewData'),{'unitId':'23466','belegungsAktion':'ANMELDUNG'},'')"
  >Anmelden</a>
</form>
<div id="form:dialogHeader:dataBox">
  <span><strong>Neural Data Science |</strong></span>
  <span>ML5401 |</span>
  <span>Veranstaltung</span>
</div>
"""

CONFIRM_HTML = """
<form id="enrollForm" action="/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&amp;_flowExecutionKey=e1s16">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="navigationPosition" value="hisinoneMeinStudium,individualTimetableSchedule" />
  <input type="hidden" name="authenticity_token" value="token-2" />
  <input type="hidden" name="enrollForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="e1s16" />
  <input type="hidden" name="planelementId" value="" />
  <table>
    <tr>
      <td>GTCN_ZR_BELEGUNG_Einfach_AN_SoSe26</td>
      <td>
        <button
          name="enrollForm:recordList:unit-Belegung:unit-BelegungTable:0:anEchtzeit"
          onclick="mojarra.jsfcljs(document.getElementById('enrollForm'),{'planelementId':'704036'},'')"
        >anmelden</button>
      </td>
    </tr>
  </table>
</form>
"""

MULTIPLE_CONFIRM_HTML = CONFIRM_HTML.replace(
    "</table>",
    """
    <tr>
      <td>Alternative module path</td>
      <td>
        <button
          name="enrollForm:recordList:unit-Belegung:unit-BelegungTable:1:anEchtzeit"
          onclick="mojarra.jsfcljs(document.getElementById('enrollForm'),{'planelementId':'704037'},'')"
        >anmelden</button>
      </td>
    </tr>
  </table>""",
)

FINAL_HTML = """
<div class="messages-infobox-scroll-container">
  <ul class="listMessages"><li>Eine Aenderung fuer Neural Data Science</li></ul>
</div>
<table><tr><td>GTCN_ZR_BELEGUNG_Einfach_AN_SoSe26</td><td>angemeldet</td></tr></table>
"""


class _FakeResponse:
    def __init__(self, *, url: str, text: str) -> None:
        self.url = url
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _RecordingSession:
    def __init__(self, *, post_responses: list[_FakeResponse]) -> None:
        self.headers: dict[str, str] = {}
        self.posts: list[dict[str, object]] = []
        self._post_responses = list(post_responses)

    def get(self, url: str, timeout: int, allow_redirects: bool = True) -> _FakeResponse:
        return _FakeResponse(url=url, text=DETAIL_HTML)

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


class AlmaCourseRegistrationTests(unittest.TestCase):
    def test_inspect_course_registration_support_extracts_detail_action(self) -> None:
        client = AlmaClient(base_url="https://alma.example", session=_RecordingSession(post_responses=[]))

        support = inspect_course_registration_support(
            client,
            "https://alma.example/alma/pages/startFlow.xhtml?unitId=23466&periodId=229",
        )

        self.assertTrue(support.supported)
        self.assertEqual(support.title, "Neural Data Science")
        self.assertEqual(support.number, "ML5401")
        self.assertEqual(support.action, "ANMELDUNG")

    def test_prepare_course_registration_opens_selector_with_multipart_start(self) -> None:
        session = _RecordingSession(
            post_responses=[_FakeResponse(url="https://alma.example/register/options", text=CONFIRM_HTML)],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        options = prepare_course_registration(client, "https://alma.example/alma/pages/startFlow.xhtml?unitId=23466&periodId=229")

        self.assertEqual(options.options[0].planelement_id, "704036")
        self.assertTrue(session.posts[0]["used_files"])
        start_payload = session.posts[0]["data"]
        self.assertEqual(start_payload["unitId"], "23466")
        self.assertEqual(start_payload["belegungsAktion"], "ANMELDUNG")
        self.assertEqual(
            start_payload["detailViewData:_idcl"],
            "detailViewData:tabContainer:further-functions-container:anmelden",
        )
        self.assertEqual(
            start_payload["detailViewData:tabContainer:term-planning-container:modules:moduleAssignments:moduleAssignmentsNavi2NumRowsInput"],
            "300",
        )

    def test_register_for_course_confirms_selected_path(self) -> None:
        session = _RecordingSession(
            post_responses=[
                _FakeResponse(url="https://alma.example/register/options", text=CONFIRM_HTML),
                _FakeResponse(url="https://alma.example/register/done", text=FINAL_HTML),
            ],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        result = register_for_course(client, "https://alma.example/alma/pages/startFlow.xhtml?unitId=23466&periodId=229")

        self.assertEqual(result.status, "registered")
        self.assertEqual(result.messages, ("Eine Aenderung fuer Neural Data Science",))
        confirm_payload = session.posts[1]["data"]
        self.assertFalse(session.posts[1]["used_files"])
        self.assertEqual(confirm_payload["planelementId"], "704036")
        self.assertEqual(confirm_payload["belegungsAktion"], "ANMELDUNG")
        self.assertEqual(
            confirm_payload["enrollForm:_idcl"],
            "enrollForm:recordList:unit-Belegung:unit-BelegungTable:0:anEchtzeit",
        )

    def test_register_for_course_requires_path_when_multiple_options_exist(self) -> None:
        session = _RecordingSession(
            post_responses=[_FakeResponse(url="https://alma.example/register/options", text=MULTIPLE_CONFIRM_HTML)],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        with self.assertRaisesRegex(AlmaParseError, "Multiple Alma course-registration paths"):
            register_for_course(client, "https://alma.example/alma/pages/startFlow.xhtml?unitId=23466&periodId=229")

    def test_register_for_course_rejects_non_alma_detail_url(self) -> None:
        client = AlmaClient(base_url="https://alma.example", session=_RecordingSession(post_responses=[]))

        with self.assertRaisesRegex(AlmaParseError, "configured Alma host"):
            register_for_course(client, "https://example.invalid/not-alma")

    def test_registration_rejects_changed_reviewed_option_before_final_post(self) -> None:
        session = _RecordingSession(post_responses=[_FakeResponse(url="https://alma.example/register/options", text=CONFIRM_HTML)])
        client = AlmaClient(base_url="https://alma.example", session=session)
        with self.assertRaisesRegex(AlmaParseError, "changed"):
            register_for_course(client, "https://alma.example/alma/pages/startFlow.xhtml", planelement_id="704036", expected_option_label="Different option")
        self.assertEqual(len(session.posts), 1)

    def test_registration_rejects_changed_reviewed_action_before_final_post(self) -> None:
        session = _RecordingSession(post_responses=[_FakeResponse(url="https://alma.example/register/options", text=CONFIRM_HTML)])
        client = AlmaClient(base_url="https://alma.example", session=session)
        from tue_api_wrapper.alma_course_registration_html import extract_registration_options
        option = extract_registration_options(CONFIRM_HTML)[0]
        with self.assertRaisesRegex(AlmaParseError, "changed"):
            register_for_course(client, "https://alma.example/alma/pages/startFlow.xhtml", planelement_id="704036", expected_option_label=option.label, expected_title="Neural Data Science", expected_number="ML5401", expected_action_name="different")
        self.assertEqual(len(session.posts), 1)


if __name__ == "__main__":
    unittest.main()
