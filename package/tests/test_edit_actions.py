from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_official_documents import (
    download_exam_report,
    download_studyservice_report,
    list_exam_reports,
)
from tue_api_wrapper.alma_timetable_pdf import render_timetable_pdf
from tue_api_wrapper.client import AlmaClient
from tue_api_wrapper.ilias_actions_client import (
    add_to_favorites,
    inspect_course_join_support,
    inspect_waitlist_support,
    join_course,
    join_waitlist,
)
from tue_api_wrapper.ilias_client import IliasClient
from tue_api_wrapper.models import CalendarOccurrence


EXAM_HTML = """
<form id="examsReadonly" action="/alma/pages/sul/examAssessment/personExamsReadonly.xhtml?_flowExecutionKey=e1s1">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="examsReadonly_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="view-1" />
  <button name="examsReadonly:exaReports:fieldset_exaReports:printReport_0">Report PDF</button>
</form>
"""

STUDYSERVICE_HTML = """
<form id="studyserviceForm" action="/alma/pages/cm/exa/enrollment/info/start.xhtml?_flowExecutionKey=e4s3">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="studyserviceForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="view-1" />
  <button name="studyserviceForm:report:reports:reportButtons:0:job2">
    <span class="jobname">Enrollment certificate</span>
  </button>
</form>
"""

STUDYSERVICE_STATUS_TAB_HTML = """
<form id="studyserviceForm" action="/alma/pages/cm/exa/enrollment/info/start.xhtml?_flowExecutionKey=e4s1">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="studyserviceForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="view-1" />
  <ul>
    <li><button type="submit" name="studyserviceForm:content.1" class="tabButton active">Einzureichende Unterlagen Aktive Registerkarte</button></li>
    <li><button type="submit" name="studyserviceForm:content.10" class="tabButton">Bescheide / Bescheinigungen</button></li>
  </ul>
</form>
"""

STUDYSERVICE_DOCUMENTS_TAB_HTML = """
<form id="studyserviceForm" action="/alma/pages/cm/exa/enrollment/info/start.xhtml?_flowExecutionKey=e4s2">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="studyserviceForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="view-2" />
  <ul>
    <li><button type="submit" name="studyserviceForm:content.1" class="tabButton">Einzureichende Unterlagen</button></li>
    <li><button type="submit" name="studyserviceForm:content.10" class="tabButton active">Bescheide / Bescheinigungen Aktive Registerkarte</button></li>
  </ul>
  <button name="studyserviceForm:report:reports:reportButtons:0:job2">
    <span class="jobname">Transcript of records</span>
  </button>
</form>
"""

JOB_CONFIG_HTML = """
<form id="studyserviceForm" action="/alma/pages/cm/exa/enrollment/info/start.xhtml?_flowExecutionKey=e4s3">
  <input type="hidden" name="activePageElementId" value="" />
  <input type="hidden" name="refreshButtonClickedId" value="" />
  <input type="hidden" name="studyserviceForm_SUBMIT" value="1" />
  <input type="hidden" name="javax.faces.ViewState" value="view-2" />
  <input name="studyserviceForm:report:reports:reportButtons:jobConfigurationButtonsOverlay:jobConfiguration:settingsContainer_0:setting_0:setting_input" value="228" />
  <button name="studyserviceForm:report:reports:reportButtons:jobConfigurationButtonsOverlay:navigationBottom:startJob" value="PDF erstellen">PDF erstellen</button>
</form>
"""

WAITLIST_HTML = """
<form action="/ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilCourseRegistrationGUI&amp;cmd=post&amp;fallbackCmd=join&amp;ref_id=5542843&amp;rtoken=abc">
  <input type="submit" name="cmd[join]" value="In Warteliste eintragen" />
</form>
"""

AGREEMENT_HTML = """
<form action="/ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilCourseRegistrationGUI&amp;cmd=post&amp;fallbackCmd=join&amp;ref_id=5542843&amp;rtoken=abc">
  <input type="checkbox" name="agreement" value="1" />
  <input type="submit" name="cmd[join]" value="In Warteliste eintragen" />
  <p>Nutzungsvereinbarung</p>
</form>
"""

WAITLIST_DONE_HTML = """
<main>
  <p>Sie sind in die Warteliste aufgenommen worden.</p>
  <p>Sie haben Platz 23 auf der Warteliste.</p>
  <p>Status der Mitgliedschaft: Eingetragen auf der Warteliste</p>
  <p>Zu dieser Nutzungsvereinbarung haben Sie ihr Einverständnis erklärt.</p>
</main>
"""

DIRECT_JOIN_HTML = """
<form action="/ilias.php?baseClass=ilrepositorygui&amp;cmdClass=ilCourseRegistrationGUI&amp;cmd=post&amp;ref_id=42&amp;rtoken=abc">
  <input type="checkbox" name="agreement" value="1" />
  <input type="submit" name="cmd[join]" value="Beitreten" />
</form>
"""

DIRECT_JOIN_DONE_HTML = """
<main><p>Sie sind dem Kurs beigetreten.</p><p>Status der Mitgliedschaft: Kursmitglied</p></main>
"""


class _FakeResponse:
    def __init__(
        self,
        *,
        url: str,
        text: str = "",
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> None:
        self.url = url
        self.text = text
        self.content = content if content is not None else text.encode()
        self.headers = headers or {"content-type": "text/html; charset=utf-8"}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"Unexpected HTTP status {self.status_code}")


class _Session:
    def __init__(self, *, gets: list[_FakeResponse] | None = None, posts: list[_FakeResponse] | None = None) -> None:
        self.headers: dict[str, str] = {}
        self.gets = list(gets or [])
        self.post_responses = list(posts or [])
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


class EditActionTests(unittest.TestCase):
    def test_render_timetable_pdf_uses_structured_view_data(self) -> None:
        view = SimpleNamespace(
            selected_term_label="Sommer 2026",
            visible_range_start=datetime(2026, 4, 13).date(),
            visible_range_end=datetime(2026, 4, 14).date(),
            occurrences=(
                CalendarOccurrence(
                    summary="Neural Data Science",
                    start=datetime(2026, 4, 13, 10, 0),
                    end=datetime(2026, 4, 13, 12, 0),
                    location="Room A",
                    description="Lecture",
                ),
            ),
        )
        with patch("tue_api_wrapper.alma_timetable_pdf.fetch_timetable_view", return_value=view):
            pdf = render_timetable_pdf(AlmaClient(base_url="https://alma.example"))

        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        self.assertEqual(pdf.content_type, "application/pdf")
        self.assertIn(b"Neural Data Science", pdf.data)
        self.assertIn("2026-04-13", pdf.filename)

    def test_exam_report_posts_print_trigger_and_returns_pdf(self) -> None:
        session = _Session(
            gets=[
                _FakeResponse(url="https://alma.example/exams", text=EXAM_HTML),
                _FakeResponse(url="https://alma.example/exams", text=EXAM_HTML),
            ],
            posts=[
                _FakeResponse(
                    url="https://alma.example/alma/rds?state=docdownload&docId=1",
                    content=b"%PDF-exam",
                    headers={"content-type": "application/pdf"},
                )
            ],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        reports = list_exam_reports(client)
        document = download_exam_report(client, trigger_name=reports[0].trigger_name)

        self.assertEqual(reports[0].label, "Report PDF")
        self.assertEqual(document.data, b"%PDF-exam")
        self.assertEqual(session.posts[0][1]["examsReadonly:_idcl"], reports[0].trigger_name)

    def test_studyservice_report_opens_job_config_and_starts_pdf_job(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://alma.example/studyservice", text=STUDYSERVICE_HTML)],
            posts=[
                _FakeResponse(url="https://alma.example/job", text=JOB_CONFIG_HTML),
                _FakeResponse(
                    url="https://alma.example/alma/rds?state=docdownload&docId=2",
                    content=b"%PDF-study",
                    headers={"content-type": "application/pdf"},
                ),
            ],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        document = download_studyservice_report(client, trigger_name="Enrollment certificate", term_id="229")

        self.assertEqual(document.data, b"%PDF-study")
        self.assertTrue(any(key.endswith(":job2") for key in session.posts[0][1]))
        start_payload = session.posts[1][1]
        self.assertEqual(start_payload["activePageElementId"].split(":")[-1], "startJob")
        setting = next(value for key, value in start_payload.items() if key.endswith(":setting_0:setting_input"))
        self.assertEqual(setting, "229")

    def test_studyservice_contract_switches_to_documents_tab(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://alma.example/studyservice", text=STUDYSERVICE_STATUS_TAB_HTML)],
            posts=[_FakeResponse(url="https://alma.example/studyservice", text=STUDYSERVICE_DOCUMENTS_TAB_HTML)],
        )
        client = AlmaClient(base_url="https://alma.example", session=session)

        page = client.fetch_studyservice_contract()

        self.assertEqual(page.active_tab_label, "Bescheide / Bescheinigungen Aktive Registerkarte")
        self.assertEqual(page.reports[0].label, "Transcript of records")
        self.assertEqual(session.posts[0][1]["activePageElementId"], "studyserviceForm:content.10")
        self.assertEqual(session.posts[0][1]["studyserviceForm:_idcl"], "studyserviceForm:content.10")

    def test_ilias_favorite_requires_add_to_desk_url(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text="<p>Favorit hinzugefügt</p>")]
        )
        client = IliasClient(session=session)

        result = add_to_favorites(
            client,
            url="https://ovidius.uni-tuebingen.de/ilias.php?cmd=addToDesk&item_ref_id=42&type=crs",
        )

        self.assertEqual(result.status, "submitted")
        self.assertEqual(session.gets, [])

    def test_ilias_waitlist_join_requires_explicit_agreement(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=WAITLIST_HTML)],
            posts=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=AGREEMENT_HTML)],
        )
        client = IliasClient(session=session)

        result = join_waitlist(
            client,
            url="https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilrepositorygui&cmdClass=ilCourseRegistrationGUI&ref_id=5542843",
        )

        self.assertEqual(result.status, "requires_agreement")
        self.assertEqual(len(session.posts), 1)

    def test_ilias_waitlist_join_accepts_agreement_when_requested(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=WAITLIST_HTML)],
            posts=[
                _FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=AGREEMENT_HTML),
                _FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=WAITLIST_DONE_HTML),
            ],
        )
        client = IliasClient(session=session)

        result = join_waitlist(
            client,
            url="https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilrepositorygui&cmdClass=ilCourseRegistrationGUI&ref_id=5542843",
            accept_agreement=True,
        )

        self.assertEqual(result.status, "joined_waitlist")
        self.assertEqual(result.waitlist_position, 23)
        self.assertEqual(session.posts[1][1]["agreement"], "1")

    def test_ilias_direct_join_preview_distinguishes_it_from_waitlist(self) -> None:
        session = _Session(gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=DIRECT_JOIN_HTML)])
        client = IliasClient(session=session)

        support = inspect_course_join_support(client, url="https://ovidius.uni-tuebingen.de/goto.php/crs/42")

        self.assertTrue(support.supported)
        self.assertTrue(support.requires_agreement)
        self.assertNotIn("rtoken", support.join_url or "")
        self.assertEqual(session.posts, [])

    def test_ilias_waitlist_preview_is_not_direct_join(self) -> None:
        waitlist_session = _Session(
            gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=WAITLIST_HTML)]
        )
        direct_session = _Session(
            gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=WAITLIST_HTML)]
        )

        waitlist = inspect_waitlist_support(
            IliasClient(session=waitlist_session),
            url="https://ovidius.uni-tuebingen.de/goto.php/crs/42",
        )
        direct = inspect_course_join_support(
            IliasClient(session=direct_session),
            url="https://ovidius.uni-tuebingen.de/goto.php/crs/42",
        )

        self.assertTrue(waitlist.supported)
        self.assertFalse(direct.supported)

    def test_ilias_direct_join_requires_explicit_agreement(self) -> None:
        session = _Session(gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=DIRECT_JOIN_HTML)])
        client = IliasClient(session=session)

        result = join_course(client, url="https://ovidius.uni-tuebingen.de/goto.php/crs/42")

        self.assertEqual(result.status, "requires_agreement")
        self.assertEqual(session.posts, [])

    def test_ilias_direct_join_submits_after_agreement(self) -> None:
        session = _Session(
            gets=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/ilias.php", text=DIRECT_JOIN_HTML)],
            posts=[_FakeResponse(url="https://ovidius.uni-tuebingen.de/goto.php/crs/42", text=DIRECT_JOIN_DONE_HTML)],
        )
        client = IliasClient(session=session)

        result = join_course(
            client,
            url="https://ovidius.uni-tuebingen.de/goto.php/crs/42",
            accept_agreement=True,
        )

        self.assertEqual(result.status, "joined")
        self.assertEqual(session.posts[0][1]["agreement"], "1")


if __name__ == "__main__":
    unittest.main()
