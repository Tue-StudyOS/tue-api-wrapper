import XCTest
@testable import TueAPI

final class UniversityPortalParsingTests: XCTestCase {
    func testIliasTaskParserExtractsDerivedTaskRows() throws {
        let pageURL = URL(string: "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilderivedtasksgui")!
        let html = """
        <html>
          <head><title>ILIAS Universität Tübingen</title></head>
          <body>
            <div class="il-item il-std-item">
              <div class="il-item-title">
                <a href="goto.php/exc_123">Assignment 4 &amp; Review</a>
              </div>
              <span class="il-item-property-name">Übung</span>
              <span class="il-item-property-value">Practical Machine Learning</span>
              <span class="il-item-property-name">Beginn</span>
              <span class="il-item-property-value">17. Apr 2026</span>
              <span class="il-item-property-name">Ende</span>
              <span class="il-item-property-value">24. Apr 2026, 23:59</span>
            </div>
          </body>
        </html>
        """

        let tasks = try IliasTaskHTMLParser.parse(html, pageURL: pageURL)

        XCTAssertEqual(tasks.count, 1)
        XCTAssertEqual(tasks[0].title, "Assignment 4 & Review")
        XCTAssertEqual(tasks[0].url, "https://ovidius.uni-tuebingen.de/goto.php/exc_123")
        XCTAssertEqual(tasks[0].itemType, "Practical Machine Learning")
        XCTAssertEqual(tasks[0].start, "17. Apr 2026")
        XCTAssertEqual(tasks[0].end, "24. Apr 2026, 23:59")
    }

    func testIliasTaskParserAcceptsAuthenticatedEmptyOverviewWithoutLegacyTitle() throws {
        let pageURL = URL(string: "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilderivedtasksgui")!
        let html = """
        <html>
          <body>
            <nav id="il-mainbar-entries"></nav>
            <main>
              <p>Keine Aufgaben vorhanden.</p>
            </main>
          </body>
        </html>
        """

        let tasks = try IliasTaskHTMLParser.parse(html, pageURL: pageURL)

        XCTAssertEqual(tasks.count, 0)
    }

    func testIliasTaskParserRejectsLoginPage() throws {
        let pageURL = URL(string: "https://ovidius.uni-tuebingen.de/login.php")!
        let passwordField = "j_" + "password"
        let html = """
        <html>
          <body>
            <form>
              <input name="j_username" />
              <input name="\(passwordField)" />
            </form>
          </body>
        </html>
        """

        XCTAssertThrowsError(try IliasTaskHTMLParser.parse(html, pageURL: pageURL)) { error in
            XCTAssertEqual(
                error.localizedDescription,
                "The response did not look like an authenticated ILIAS task overview."
            )
        }
    }

    func testIliasContentParserExtractsCourseExerciseItems() throws {
        let pageURL = URL(string: "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilrepositorygui&ref_id=5551408")!
        let html = """
        <html>
          <head><title>Practical Machine Learning: Ovidius Universität Tübingen</title></head>
          <body>
            <div class="ilContainerBlock form-inline">
              <div class="ilContainerBlockHeader"><h2>Übungen</h2></div>
              <div class="ilContainerListItemOuter">
                <div class="ilContainerListItemIcon"><img alt="Übung" src="icon_exc.svg"></div>
                <h3 class="il_ContainerItemTitle">
                  <a class="il_ContainerItemTitle" href="goto.php/exc/5653468">Assignments</a>
                </h3>
                <span class="il_ItemProperty">Nächste Abgabefrist: 2 Tage</span>
              </div>
            </div>
          </body>
        </html>
        """

        let page = try IliasContentHTMLParser.parse(html, pageURL: pageURL)

        XCTAssertEqual(page.sections.map(\.label), ["Übungen"])
        XCTAssertEqual(page.sections[0].items[0].label, "Assignments")
        XCTAssertEqual(page.sections[0].items[0].kind, "Übung")
        XCTAssertEqual(page.sections[0].items[0].url, "https://ovidius.uni-tuebingen.de/goto.php/exc/5653468")
        XCTAssertTrue(IliasCourseAssignmentsBuilder.isExerciseItem(page.sections[0].items[0]))
    }

    func testIliasExerciseAssignmentParserExtractsPracticeExamShape() throws {
        let pageURL = URL(string: "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilexercisehandlergui&ref_id=5653468")!
        let html = """
        <div class="il-item il-std-item">
          <div class="row">
            <div class="col-sm-3">In 2 Tage, 13 Stunden abzugeben</div>
            <div class="col-sm-9">
              <h4 class="il-item-title">
                <a href="ilias.php?cmdClass=ilAssignmentPresentationGUI&amp;ass_id=97583">Assignment_5_submission</a>
              </h4>
              <button data-action="ilias.php?cmdClass=ilExSubmissionFileGUI&amp;cmd=submissionScreen&amp;ass_id=97583">
                Datei abgeben
              </button>
              <span class="il-item-property-name">Abgabetermin</span>
              <span class="il-item-property-value">19. Jun 2026, 00:00</span>
              <span class="il-item-property-name">Anforderung</span>
              <span class="il-item-property-value">Verpflichtend</span>
              <span class="il-item-property-name">Datum der letzten Abgabe</span>
              <span class="il-item-property-value">Bisher keine Abgabe</span>
              <span class="il-item-property-name">Type</span>
              <span class="il-item-property-value">Datei</span>
              <span class="il-item-property-name">Status</span>
              <span class="il-item-property-value">Nicht bewertet</span>
            </div>
          </div>
        </div>
        """

        let assignments = try IliasExerciseAssignmentHTMLParser.parse(html, pageURL: pageURL)

        XCTAssertEqual(assignments.count, 1)
        XCTAssertEqual(assignments[0].title, "Assignment_5_submission")
        XCTAssertEqual(assignments[0].dueHint, "In 2 Tage, 13 Stunden abzugeben")
        XCTAssertEqual(assignments[0].dueAt, "19. Jun 2026, 00:00")
        XCTAssertEqual(assignments[0].status, "Nicht bewertet")
        XCTAssertTrue(assignments[0].teamActionURL?.contains("submissionScreen") == true)
    }

    func testMoodleCalendarNormalizerExtractsActionableEvents() throws {
        let baseURL = URL(string: "https://moodle.zdv.uni-tuebingen.de")!
        let payload = """
        [{
          "error": false,
          "data": {
            "events": [{
              "id": 42,
              "name": "Essay submission",
              "timesort": 1777071540,
              "formattedtime": "Due Friday, 24 April 2026, 23:59",
              "course": {"id": 7, "fullname": "Probabilistic Machine Learning"},
              "action": {"url": "/mod/assign/view.php?id=99"}
            }]
          }
        }]
        """.data(using: .utf8)!

        let deadlines = try MoodleCalendarNormalizer.deadlines(from: payload, baseURL: baseURL)

        XCTAssertEqual(deadlines.count, 1)
        XCTAssertEqual(deadlines[0].rawId, 42)
        XCTAssertEqual(deadlines[0].title, "Essay submission")
        XCTAssertEqual(deadlines[0].formattedTime, "Due Friday, 24 April 2026, 23:59")
        XCTAssertEqual(deadlines[0].courseName, "Probabilistic Machine Learning")
        XCTAssertEqual(deadlines[0].courseId, 7)
        XCTAssertEqual(deadlines[0].actionURL, "https://moodle.zdv.uni-tuebingen.de/mod/assign/view.php?id=99")
        XCTAssertTrue(deadlines[0].isActionable)
    }

    func testMoodleCalendarNormalizerThrowsMoodleErrorMessage() throws {
        let baseURL = URL(string: "https://moodle.zdv.uni-tuebingen.de")!
        let payload = """
        [{"error": true, "exception": "Invalid sesskey"}]
        """.data(using: .utf8)!

        XCTAssertThrowsError(try MoodleCalendarNormalizer.deadlines(from: payload, baseURL: baseURL)) { error in
            XCTAssertEqual(error.localizedDescription, "Invalid sesskey")
        }
    }

    func testAlmaPortalMessagesParserExtractsVisibleMitteilungen() throws {
        let pageURL = URL(string: "https://alma.uni-tuebingen.de/alma/pages/cs/sys/portal/hisinoneStartPage.faces")!
        let partial = """
        <partial-response><changes>
          <update id="startPage:portletInstanceId_1013311:portletInstanceId_1013311"><![CDATA[
            <div class="portalMessagesContent">
              <ul>
                <li class="menu menuList">
                  <div class="menuWrap">
                    <img src="/HISinOne/images/icons/print_pdf.svg" />
                    <a href="/alma/pages/startFlow.xhtml?_flowId=document-download-flow&amp;doc=4557346" target="_blank">
                      <div class="portalMessageText">In Ihrem Bewerbungsportal ist ein neues Dokument verfügbar.</div>
                    </a>
                    <small class="menuListDate">04.05.2026 - 18:32 Uhr</small>
                    <button onclick="jsf.ajax.request(this,event,{'messageId':'7694275'})"></button>
                  </div>
                </li>
              </ul>
            </div>
          ]]></update>
        </changes></partial-response>
        """

        let page = try AlmaPortalMessagesHTMLParser.parsePartialResponse(partial, pageURL: pageURL)

        XCTAssertEqual(page.items.count, 1)
        XCTAssertEqual(page.items[0].id, "7694275")
        XCTAssertEqual(page.items[0].target, "_blank")
        XCTAssertEqual(page.items[0].createdAtLabel, "04.05.2026 - 18:32 Uhr")
        XCTAssertEqual(
            page.items[0].url,
            "https://alma.uni-tuebingen.de/alma/pages/startFlow.xhtml?_flowId=document-download-flow&doc=4557346"
        )
    }
}
