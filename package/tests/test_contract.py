from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.alma_documents_html import extract_studyservice_page
from tue_api_wrapper.alma_academics_html import (
    extract_advanced_module_search_form,
    parse_module_detail_page,
    parse_course_catalog_page,
    parse_enrollment_page,
    parse_exam_overview,
    parse_module_search_page,
    parse_module_search_results_page,
)
from tue_api_wrapper.client import AlmaClient
from tue_api_wrapper.html_contract import (
    build_term_export_url,
    extract_login_form,
    extract_timetable_export_url,
    extract_timetable_terms,
)
from tue_api_wrapper.ilias_html import (
    extract_hidden_form,
    extract_idp_login_form,
    parse_ilias_content_page,
    extract_shib_login_url,
    parse_ilias_root_page,
)
from tue_api_wrapper.ilias_learning_html import (
    parse_exercise_assignments,
    parse_forum_topics,
    parse_membership_overview,
    parse_task_overview,
)
from tue_api_wrapper.ics import (
    parse_ics_events,
    expand_ics_events,
)
from tue_api_wrapper.route_discovery_cli import discover_routes


class _FakeResponse:
    def __init__(self, *, url: str, text: str, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        self.url = url
        self.text = text
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html; charset=utf-8"}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} for {self.url}")


class _FakeSession:
    def __init__(self, pages: dict[str, _FakeResponse]) -> None:
        self._pages = pages

    def get(self, url: str, timeout: int, allow_redirects: bool = True) -> _FakeResponse:
        try:
            return self._pages[url]
        except KeyError as exc:
            raise requests.RequestException(f"Missing fixture for {url}") from exc


def _har_response_text(har_path: Path, predicate) -> str:
    payload = json.loads(har_path.read_text(encoding="utf-8"))
    for entry in payload["log"]["entries"]:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {})
        if predicate(request):
            return entry.get("response", {}).get("content", {}).get("text", "")
    raise AssertionError(f"No HAR entry matched for {har_path.name}")


def _require_fixture(test_case: unittest.TestCase, fixture_name: str) -> Path:
    fixture_path = ROOT / "fixtures" / fixture_name
    if not fixture_path.exists():
        test_case.skipTest(
            f"Local network fixture '{fixture_name}' is not available. "
            "HAR captures are intentionally kept out of version control."
        )
    return fixture_path


class AlmaContractTests(unittest.TestCase):
    def test_login_form_contract_can_be_extracted(self) -> None:
        html = """
        <html>
          <body class="notloggedin">
            <form
              id="loginForm"
              action="https://alma.uni-tuebingen.de:443/alma/rds?state=user&amp;type=1&amp;category=auth.login"
            >
              <input type="hidden" name="userInfo" value="" />
              <input type="hidden" name="ajax-token" value="token-123" />
              <input type="text" name="asdf" value="" />
              <input type="password" name="fdsa" value="" />
              <button type="submit" name="submit"></button>
            </form>
          </body>
        </html>
        """
        login_form = extract_login_form(
            html=html,
            page_url="https://alma.uni-tuebingen.de/alma/pages/cs/sys/portal/hisinoneStartPage.faces",
        )

        self.assertIn("category=auth.login", login_form.action_url)
        self.assertIn("ajax-token", login_form.payload)
        self.assertIn("userInfo", login_form.payload)

    def test_timetable_contract_contains_summer_2026_and_export_url(self) -> None:
        html = _har_response_text(
            _require_fixture(self, "alma2.uni-tuebingen.de.har"),
            lambda request: request.get("method") == "GET"
            and "_flowExecutionKey=e2s1" in request.get("url", ""),
        )
        terms = extract_timetable_terms(html)
        export_url = extract_timetable_export_url(html)

        self.assertEqual(terms["Sommer 2026"], "229")
        self.assertIn("individualTimetableCalendarExport.faces", export_url)
        self.assertEqual(build_term_export_url(export_url, "229").split("termgroup=")[-1], "229")

    def test_ics_parser_expands_simple_rrule(self) -> None:
        raw_ics = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VEVENT",
                "UID:test-1",
                "SUMMARY:Machine Learning Seminar",
                "DTSTART;TZID=Europe/Berlin:20260413T101500",
                "DTEND;TZID=Europe/Berlin:20260413T114500",
                "RRULE:FREQ=WEEKLY;COUNT=3",
                "LOCATION:Sand 14",
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )

        events = parse_ics_events(raw_ics)
        occurrences = expand_ics_events(events, "Sommer 2026")

        self.assertEqual(len(events), 1)
        self.assertEqual(len(occurrences), 3)
        self.assertEqual(occurrences[0].summary, "Machine Learning Seminar")
        self.assertEqual(occurrences[0].location, "Sand 14")

    def test_ics_parser_normalizes_local_until_for_timezone_aware_events(self) -> None:
        raw_ics = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VEVENT",
                "UID:test-2",
                "SUMMARY:Ethics and Philosophy of Machine Learning",
                "DTSTART;TZID=Europe/Berlin:20260413T120000",
                "DTEND;TZID=Europe/Berlin:20260413T140000",
                "RRULE:FREQ=WEEKLY;UNTIL=20260427T140000;BYDAY=MO",
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )

        events = parse_ics_events(raw_ics)
        occurrences = expand_ics_events(events, "Sommer 2026")

        self.assertEqual(
            [item.start.date().isoformat() for item in occurrences],
            ["2026-04-13", "2026-04-20", "2026-04-27"],
        )

    def test_summer_term_window_excludes_winter_events(self) -> None:
        raw_ics = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VEVENT",
                "UID:winter-only",
                "SUMMARY:Winter Block",
                "DTSTART;TZID=Europe/Berlin:20260112T120000",
                "DTEND;TZID=Europe/Berlin:20260112T140000",
                "END:VEVENT",
                "BEGIN:VEVENT",
                "UID:summer-only",
                "SUMMARY:Summer Block",
                "DTSTART;TZID=Europe/Berlin:20260413T120000",
                "DTEND;TZID=Europe/Berlin:20260413T140000",
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )

        events = parse_ics_events(raw_ics)
        occurrences = expand_ics_events(events, "Sommer 2026")

        self.assertEqual([item.summary for item in occurrences], ["Summer Block"])

    def test_calendar_response_prefers_utf8_decoding(self) -> None:
        response = requests.Response()
        response._content = "alma-Einführung für neue Studierende".encode("utf-8")
        response.encoding = "ISO-8859-1"

        self.assertEqual(
            AlmaClient._decode_calendar_response(response),
            "alma-Einführung für neue Studierende",
        )

    def test_studyservice_contract_contains_report_jobs_and_download_link(self) -> None:
        html = _har_response_text(
            _require_fixture(self, "alma.documents.uni-tuebingen.de.har"),
            lambda request: request.get("method") == "GET"
            and "_flowExecutionKey=e4s3" in request.get("url", ""),
        )
        contract = extract_studyservice_page(
            html,
            "https://alma.uni-tuebingen.de/alma/pages/cm/exa/enrollment/info/start.xhtml?_flowId=studyservice-flow&_flowExecutionKey=e4s3",
        )

        labels = [report.label for report in contract.reports]
        self.assertEqual(len(contract.reports), 6)
        self.assertIn("Immatrikulationsbescheinigung/Studienbescheinigung/Datenkontrollblatt [PDF]", labels)
        self.assertIn(
            "state=docdownload&docId=73ecf0f5-68e5-4152-8651-4e5c379b1429",
            contract.latest_download_url,
        )

    def test_download_filename_uses_content_disposition(self) -> None:
        response = requests.Response()
        response.status_code = 200
        response.url = "https://alma-up.uni-tuebingen.de/alma/rds?state=docdownload&docName=fallback.pdf"
        response.headers["content-disposition"] = (
            'attachment; filename="ignored.pdf"; '
            "filename*=utf-8''Immatrikulationsbescheinigung%20%5BPDF%5D.pdf"
        )

        self.assertEqual(
            AlmaClient._extract_download_filename(response, response.url),
            "Immatrikulationsbescheinigung [PDF].pdf",
        )

    def test_parse_enrollment_page_extracts_terms_and_message(self) -> None:
        html = """
        <form id="studentOverviewForm">
          <select name="studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input">
            <option value="220">Wintersemester 2025/26</option>
            <option value="229" selected="selected">Sommersemester 2026</option>
          </select>
          <div>Sie haben bisher keine Veranstaltungen belegt und keine Prüfungen angemeldet.</div>
        </form>
        """
        page = parse_enrollment_page(html)
        self.assertEqual(page.selected_term, "Sommersemester 2026")
        self.assertEqual(page.available_terms["Sommersemester 2026"], "229")
        self.assertIn("keine Veranstaltungen", page.message)

    def test_parse_exam_overview_extracts_tree_rows(self) -> None:
        html = """
        <table class="treeTableWithIcons">
          <tr><th>Titel</th></tr>
          <tr class="treeTableCellLevel3">
            <td class="invisible">1.1.1.1</td>
            <td></td><td></td><td></td>
            <td colspan="2"><img class="submitImageTable" alt="Konto"/><span id="x:unDeftxt">Studienbegleitende Leistungen</span></td>
            <td><span id="x:elementnr">9055</span></td>
            <td><span id="x:attempt">1</span></td>
            <td></td>
            <td><span id="x:grade">1,0</span></td>
            <td><span id="x:bonus">9</span></td>
            <td><span id="x:malus">0</span></td>
            <td><span id="x:workstatus">BE</span></td>
            <td><span id="x:freeTrial">-</span></td>
            <td><span id="x:remark"></span></td>
            <td><span id="x:exceptionNein">Nein</span></td>
            <td></td>
            <td><span id="x:geplantesFreigabedatum">2026-02-01</span></td>
            <td></td>
          </tr>
        </table>
        """
        rows = parse_exam_overview(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].title, "Studienbegleitende Leistungen")
        self.assertEqual(rows[0].number, "9055")
        self.assertEqual(rows[0].status, "BE")

    def test_parse_course_catalog_page_extracts_nodes(self) -> None:
        html = """
        <table class="treeTableWithIcons">
          <tr class="treeTableCellLevel1">
            <td class="invisible">1.2</td>
            <td></td>
            <td><button class="treeTableIcon" type="submit"></button></td>
            <td colspan="20">
              <span class="treeElementName"><img class="imagetop" alt="Überschriftenelement"/>
                <span id="x:ot_3">7 Mathematisch-Naturwissenschaftliche Fakultät</span>
              </span>
            </td>
            <td><input id="autologinRequestUrl" value="https://alma.example/catalog/7"/></td>
          </tr>
        </table>
        """
        rows = parse_course_catalog_page(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].title, "7 Mathematisch-Naturwissenschaftliche Fakultät")
        self.assertEqual(rows[0].permalink, "https://alma.example/catalog/7")
        self.assertTrue(rows[0].expandable)

    def test_parse_module_search_page_extracts_query_form_and_results(self) -> None:
        html = """
        <form id="genericSearchMask" action="/alma/search">
          <input type="hidden" name="javax.faces.ViewState" value="e1s2" />
          <input type="text" name="genericSearchMask:search_foo:cm_exa_searchModuleDescription_characteristics:fieldset:inputField_0_bar:idbar" value="" />
          <input type="hidden" name="genericSearchMask_SUBMIT" value="1" />
        </form>
        <table class="tableWithBorder">
          <tr><th>Aktionen</th><th>Nummer</th><th>Titel</th><th>Elementtyp</th></tr>
          <tr><td><a href="/alma/detail/1">Details</a></td><td>ML4201</td><td>Statistical Machine Learning</td><td>Veranstaltung</td></tr>
        </table>
        """
        page = parse_module_search_page(html, "https://alma.example/search")
        self.assertIn("searchModuleDescription", page.form.query_field_name)
        self.assertEqual(page.results[0].title, "Statistical Machine Learning")
        self.assertEqual(page.results[0].element_type, "Veranstaltung")

    def test_extract_advanced_module_search_form_extracts_public_filters(self) -> None:
        html = """
        <form id="genericSearchMask" action="/alma/search">
          <button type="submit" name="genericSearchMask:buttonsBottom:search"><span>Suchen</span></button>
          <button type="submit" name="genericSearchMask:buttonsBottom:toggleSearchShowAllCriteria"><span>Erweiterte Suche</span></button>
          <input type="hidden" name="javax.faces.ViewState" value="e1s2" />
          <div>
            <label class="form-label" for="query">Suchbegriffe</label>
            <input id="query" type="text" name="query_name" value="" />
          </div>
          <div>
            <label class="form-label" for="degree-focus">Abschluss</label>
            <input id="degree-focus" type="text" name="degree_focus" value="" />
            <select name="degree_not_input">
              <option value="">=</option>
            </select>
            <select name="degree_input">
              <option value=""></option>
              <option value="89">Master</option>
              <option value="83">Bachelor</option>
            </select>
          </div>
          <div>
            <label class="form-label" for="subject-focus">Fach</label>
            <input id="subject-focus" type="text" name="subject_focus" value="" />
            <select name="subject_not_input">
              <option value="">=</option>
            </select>
            <select name="subject_input">
              <option value=""></option>
              <option value="2385">Informatik / Computer Science</option>
              <option value="2365">Machine Learning</option>
            </select>
          </div>
        </form>
        """
        contract = extract_advanced_module_search_form(html, "https://alma.example/search")

        self.assertEqual(contract.query_field_name, "query_name")
        self.assertEqual(contract.search_button_name, "genericSearchMask:buttonsBottom:search")
        self.assertEqual(contract.toggle_advanced_button_name, "genericSearchMask:buttonsBottom:toggleSearchShowAllCriteria")
        self.assertEqual([item.label for item in contract.filters.degrees], ["Master", "Bachelor"])
        self.assertEqual([item.label for item in contract.filters.subjects], ["Informatik / Computer Science", "Machine Learning"])

    def test_parse_module_search_results_page_extracts_counts_and_pager_controls(self) -> None:
        html = """
        <form id="genSearchRes" action="/alma/results">
          <input type="hidden" name="javax.faces.ViewState" value="e1s3" />
          <input type="hidden" name="genSearchRes_SUBMIT" value="1" />
          <input type="number" name="genSearchRes:table:Navi2NumRowsInput" value="100" />
          <button type="submit" name="genSearchRes:table:Navi2NumRowsRefresh"></button>
        </form>
        <table class="tableWithBorder">
          <tr><th>Aktionen</th><th>Nummer</th><th>Titel</th><th>Elementtyp</th></tr>
          <tr><td><a href="/alma/detail/1">Details</a></td><td>ML4201</td><td>Statistical Machine Learning</td><td>Veranstaltung</td></tr>
        </table>
        <span class="dataScrollerResultText">124 Ergebnisse</span>
        <span class="dataScrollerPageText">Seite 1 von 2</span>
        """
        page = parse_module_search_results_page(html, "https://alma.example/results")

        self.assertEqual(page.total_results, 124)
        self.assertEqual(page.total_pages, 2)
        self.assertEqual(page.rows_input_name, "genSearchRes:table:Navi2NumRowsInput")
        self.assertEqual(page.rows_refresh_name, "genSearchRes:table:Navi2NumRowsRefresh")
        self.assertEqual(page.results[0].title, "Statistical Machine Learning")

    def test_parse_module_detail_page_extracts_basic_data_and_tabs(self) -> None:
        html = """
        <input id="autologinRequestUrl" value="https://alma.example/detail/1" />
        <button class="active tabButton immediate" type="submit" value="Modulbeschreibung">
          <span>Modulbeschreibung</span><span>Aktive Registerkarte</span>
        </button>
        <button class="inactive tabButton immediate" type="submit" value="Studiengänge">
          <span>Studiengänge</span>
        </button>
        <div class="boxStandard" id="detailViewData:basicData:fieldset">
          <div class="box_title"><h2>Grunddaten</h2></div>
          <div class="box_content">
            <div class="labelItemLine">
              <label>Titel</label>
              <div class="answer">Efficient Machine Learning in Hardware</div>
            </div>
            <div class="labelItemLine">
              <label>Nummer</label>
              <div class="answer">ML-4420</div>
            </div>
            <div class="labelItemLine">
              <label>Einrichtungen</label>
              <div class="answer">Mathematisch-Naturwissenschaftliche Fakultät</div>
            </div>
          </div>
        </div>
        <div class="boxStandard" id="detailViewData:moduleStudyPrograms:fieldset">
          <div class="box_title"><h2>Module / Studiengänge</h2></div>
          <div class="box_content">
            <table>
              <tr><th>Studiengang</th><th>Abschluss</th><th>Modul</th></tr>
              <tr><td>Informatik</td><td>Master</td><td>INFO-ML</td></tr>
            </table>
          </div>
        </div>
        """
        detail = parse_module_detail_page(html, "https://alma.example/detail/1")

        self.assertEqual(detail.title, "Efficient Machine Learning in Hardware")
        self.assertEqual(detail.number, "ML-4420")
        self.assertEqual(detail.permalink, "https://alma.example/detail/1")
        self.assertEqual(detail.active_tab, "Modulbeschreibung")
        self.assertEqual(detail.available_tabs, ("Modulbeschreibung", "Studiengänge"))
        self.assertEqual(detail.sections[0].title, "Grunddaten")
        self.assertEqual(detail.module_study_program_tables[0].title, "Module / Studiengänge")
        self.assertEqual(detail.module_study_program_tables[0].headers, ("Studiengang", "Abschluss", "Modul"))
        self.assertEqual(detail.module_study_program_tables[0].rows[0], ("Informatik", "Master", "INFO-ML"))

    def test_ilias_login_parsers(self) -> None:
        login_html = """
        <html><body>
          <a href="shib_login.php?target=">&gt;&gt; Login mit zentraler Universitäts-Kennung &lt;&lt;</a>
        </body></html>
        """
        self.assertEqual(
            extract_shib_login_url(login_html, "https://ovidius.uni-tuebingen.de/login.php?cmd=force_login"),
            "https://ovidius.uni-tuebingen.de/shib_login.php?target=",
        )

        idp_html = """
        <html><body>
          <form action="/idp/profile/SAML2/Redirect/SSO?execution=e1s1" method="post">
            <input name="j_username" type="text" value="" />
            <input name="j_password" type="password" value="" />
            <button name="_eventId_proceed" type="submit">Login</button>
          </form>
        </body></html>
        """
        idp_form = extract_idp_login_form(idp_html, "https://idp.uni-tuebingen.de/idp/profile/SAML2/Redirect/SSO?execution=e1s1")
        self.assertIn("execution=e1s1", idp_form.action_url)
        self.assertIn("j_username", idp_form.payload)
        self.assertIn("j_password", idp_form.payload)

        saml_html = """
        <html><body>
          <form action="https://ovidius.uni-tuebingen.de/Shibboleth.sso/SAML2/POST" method="post">
            <input type="hidden" name="RelayState" value="relay" />
            <input type="hidden" name="SAMLResponse" value="assertion" />
          </form>
        </body></html>
        """
        saml_form = extract_hidden_form(saml_html, "https://idp.uni-tuebingen.de/idp/profile/SAML2/Redirect/SSO?execution=e1s2", {"RelayState", "SAMLResponse"})
        self.assertEqual(saml_form.payload["RelayState"], "relay")

    def test_ilias_root_page_parser_uses_har(self) -> None:
        html = _har_response_text(
            _require_fixture(self, "ovidius.uni-tuebingen.de.har"),
            lambda request: request.get("method") == "GET"
            and request.get("url") == "https://ovidius.uni-tuebingen.de/ilias3/ilias.php?baseClass=ilrepositorygui&ref_id=1",
        )
        root_page = parse_ilias_root_page(html, "https://ovidius.uni-tuebingen.de/ilias3/ilias.php?baseClass=ilrepositorygui&ref_id=1")

        self.assertIn("ILIAS", root_page.title)
        self.assertTrue(any(link.label == "Dashboard" for link in root_page.mainbar_links))
        self.assertTrue(any(link.label == "Sommersemester 2026" for link in root_page.top_categories))

    def test_ilias_content_page_parser_uses_har(self) -> None:
        html = _har_response_text(
            _require_fixture(self, "ovidius2.uni-tuebingen.de.har"),
            lambda request: request.get("method") == "GET"
            and request.get("url") == "https://ovidius.uni-tuebingen.de/ilias3/ilias.php?baseClass=ilrepositorygui&ref_id=5289871",
        )
        page = parse_ilias_content_page(
            html,
            "https://ovidius.uni-tuebingen.de/ilias3/ilias.php?baseClass=ilrepositorygui&ref_id=5289871",
        )

        self.assertIn("MPC Materials", page.title)
        self.assertEqual([section.label for section in page.sections], ["Foren", "Weblinks", "Übungen"])
        labels = [item.label for section in page.sections for item in section.items]
        self.assertIn("MPC Forum", labels)
        self.assertIn("Link to Slides and Recordings", labels)
        self.assertIn("Exercises", labels)

    def test_parse_forum_topics_extracts_properties(self) -> None:
        html = """
        <div class="il-item il-std-item">
          <h4 class="il-item-title"><a href="thread/1">Question 1</a></h4>
          <span class="il-item-property-name">Angelegt von</span><span class="il-item-property-value">Alice</span>
          <span class="il-item-property-name">Beiträge</span><span class="il-item-property-value">3</span>
          <span class="il-item-property-name">Letzter Beitrag</span><span class="il-item-property-value">2026-03-09</span>
          <span class="il-item-property-name">Besuche</span><span class="il-item-property-value">12</span>
        </div>
        """
        topics = parse_forum_topics(html, "https://ovidius.example/forum")
        self.assertEqual(topics[0].title, "Question 1")
        self.assertEqual(topics[0].author, "Alice")
        self.assertEqual(topics[0].posts, "3")

    def test_parse_exercise_assignments_extracts_properties(self) -> None:
        html = """
        <div class="il-item il-std-item">
          <div class="col-sm-3">In 2 Tagen abzugeben</div>
          <div class="col-sm-9">
            <h4 class="il-item-title"><a href="assignment/1">Exercise01</a></h4>
            <button data-action="team/create"></button>
            <span class="il-item-property-name">Abgabetermin</span><span class="il-item-property-value">Freitag, 12:00</span>
            <span class="il-item-property-name">Anforderung</span><span class="il-item-property-value">Verpflichtend</span>
            <span class="il-item-property-name">Datum der letzten Abgabe</span><span class="il-item-property-value">Bisher keine Abgabe</span>
            <span class="il-item-property-name">Type</span><span class="il-item-property-value">Datei</span>
            <span class="il-item-property-name">Status</span><span class="il-item-property-value">Nicht bewertet</span>
          </div>
        </div>
        """
        assignments = parse_exercise_assignments(html, "https://ovidius.example/exc")
        self.assertEqual(assignments[0].title, "Exercise01")
        self.assertEqual(assignments[0].due_at, "Freitag, 12:00")
        self.assertEqual(assignments[0].team_action_url, "https://ovidius.example/team/create")

    def test_parse_membership_overview_extracts_items(self) -> None:
        html = """
        <div class="il-item il-std-item">
          <div class="media">
            <div class="media-left"><img alt="Kurs" /></div>
            <div class="media-body">
              <h4 class="il-item-title"><a href="goto.php/crs/5278426">Data Literacy (ML 4102)</a></h4>
              <div class="il-item-description">This course conveys the basic techniques of quantitative thinking.</div>
              <button data-action="ilias.php?baseClass=ilrepositorygui&amp;cmd=infoScreen&amp;ref_id=5278426">Info</button>
              <div class="row">
                <div class="col-md-6">
                  <span class="il-item-property-name">Anmeldungszeitraum</span><span class="il-item-property-value">Keine Anmeldung möglich</span>
                </div>
                <div class="col-md-6">
                  <span class="il-item-property-name">Veranstaltungszeitraum</span><span class="il-item-property-value">14. Okt 2025 - 10. Feb 2026</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        """
        items = parse_membership_overview(html, "https://ovidius.example/ilias.php?baseClass=ilmembershipoverviewgui")

        self.assertEqual(items[0].title, "Data Literacy (ML 4102)")
        self.assertEqual(items[0].kind, "Kurs")
        self.assertIn("quantitative thinking", items[0].description)
        self.assertEqual(
            items[0].info_url,
            "https://ovidius.example/ilias.php?baseClass=ilrepositorygui&cmd=infoScreen&ref_id=5278426",
        )
        self.assertIn("Veranstaltungszeitraum: 14. Okt 2025 - 10. Feb 2026", items[0].properties)

    def test_parse_task_overview_extracts_due_items(self) -> None:
        html = """
        <div class="il-item il-std-item">
          <h4 class="il-item-title">
            <button data-action="goto.php/exc/5509760/93823">Abgabe zur Übungseinheit "Exercise05"</button>
          </h4>
          <div class="row">
            <div class="col-md-6">
              <span class="il-item-property-name">Übung</span><span class="il-item-property-value">Exercises</span>
            </div>
            <div class="col-md-6">
              <span class="il-item-property-name">Beginn</span><span class="il-item-property-value">Heute, 10:30</span>
            </div>
          </div>
          <div class="row">
            <div class="col-md-6">
              <span class="il-item-property-name">Ende</span><span class="il-item-property-value">Morgen, 12:00</span>
            </div>
          </div>
        </div>
        """
        items = parse_task_overview(html, "https://ovidius.example/ilias.php?baseClass=ilderivedtasksgui")

        self.assertEqual(items[0].title, 'Abgabe zur Übungseinheit "Exercise05"')
        self.assertEqual(items[0].item_type, "Exercises")
        self.assertEqual(items[0].start, "Heute, 10:30")
        self.assertEqual(items[0].end, "Morgen, 12:00")
        self.assertEqual(items[0].url, "https://ovidius.example/goto.php/exc/5509760/93823")

    def test_route_discovery_collects_links_forms_and_script_hints(self) -> None:
        session = _FakeSession(
            {
                "https://alma.example/start": _FakeResponse(
                    url="https://alma.example/start",
                    text="""
                    <html>
                      <head><title>Start</title></head>
                      <body>
                        <a href="/alma/pages/search.xhtml?degree=89&subject=2385">Search</a>
                        <form action="/alma/api/filter" method="post">
                          <input type="hidden" name="javax.faces.ViewState" value="e1s2" />
                          <input type="text" name="query" value="" />
                          <button type="submit" name="search">Search</button>
                        </form>
                        <script>
                          window.__routes = ["/alma/pages/detail.xhtml?module=ML-4420"];
                        </script>
                      </body>
                    </html>
                    """,
                ),
                "https://alma.example/alma/pages/search.xhtml?degree=89&subject=2385": _FakeResponse(
                    url="https://alma.example/alma/pages/search.xhtml?degree=89&subject=2385",
                    text="""
                    <html>
                      <head><title>Search</title></head>
                      <body>
                        <a href="/alma/pages/detail.xhtml?module=ML-4420">Detail</a>
                      </body>
                    </html>
                    """,
                ),
                "https://alma.example/alma/pages/detail.xhtml?module=ML-4420": _FakeResponse(
                    url="https://alma.example/alma/pages/detail.xhtml?module=ML-4420",
                    text="<html><head><title>Detail</title></head><body></body></html>",
                ),
            }
        )

        report = discover_routes(
            session=session,
            start_urls=("https://alma.example/start",),
            allowed_hosts={"alma.example"},
            depth=1,
            max_pages=5,
            request_timeout=5,
        )

        paths = {(route["path"], tuple(route["query_keys"])): route for route in report["routes"]}
        self.assertIn(("/alma/pages/search.xhtml", ("degree", "subject")), paths)
        self.assertIn(("/alma/api/filter", ()), paths)
        self.assertIn(("/alma/pages/detail.xhtml", ("module",)), paths)

        form = report["forms"][0]
        self.assertEqual(form["action_url"], "https://alma.example/alma/api/filter")
        self.assertEqual(form["method"], "POST")
        self.assertEqual(form["field_names"], ["javax.faces.ViewState", "query"])
        self.assertEqual(form["button_names"], ["search"])


if __name__ == "__main__":
    unittest.main()
