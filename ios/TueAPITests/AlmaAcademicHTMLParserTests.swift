import XCTest
@testable import TueAPI

final class AlmaAcademicHTMLParserTests: XCTestCase {
    func testParsesEnrollmentTermsAndMessage() throws {
        let html = """
        <form id="studentOverviewForm">
          <select name="studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input">
            <option value="20241">Winter 2024/25</option>
            <option value="20251" selected="selected">Summer 2025</option>
          </select>
          <p>Sie haben bisher fuer diesen Studiengang keine Anmeldung zugelassen.</p>
        </form>
        <h2>Personendaten: Sebastian Böhler</h2>
        """

        let enrollment = try AlmaAcademicHTMLParser.parseEnrollment(html)

        XCTAssertEqual(enrollment.selectedTerm, "Summer 2025")
        XCTAssertEqual(enrollment.availableTerms["Winter 2024/25"], "20241")
        XCTAssertEqual(enrollment.message, "Sie haben bisher fuer diesen Studiengang keine Anmeldung zugelassen.")
        XCTAssertEqual(enrollment.personName, "Sebastian Böhler")
        XCTAssertTrue(enrollment.entries.isEmpty)
    }

    func testParsesBelegungenRowsWithExamDetails() throws {
        let html = """
        <form id="studentOverviewForm">
          <select name="studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input">
            <option value="2026.2.1" selected="selected">Sommersemester 2026</option>
          </select>
          <h2>Veranstaltung: Vorlesung/Übung GTCNEURO Neural Data Science</h2>
          <table>
            <tr>
              <td>Termine und Räume Status Aktionen 1. Parallelgruppe Neural Data Science jeden Mittwoch (15.04.26 bis 22.07.26) von 10:15 bis 11:45 wöchentlich Details anzeigen</td>
              <td>Ihr aktueller Status: storniert Semester der Leistung: SoSe 2026</td>
            </tr>
          </table>
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

        let enrollment = try AlmaAcademicHTMLParser.parseEnrollment(html)

        XCTAssertEqual(enrollment.entries.count, 2)
        XCTAssertEqual(enrollment.entries[0].category, "Veranstaltung")
        XCTAssertEqual(enrollment.entries[0].eventType, "Vorlesung/Übung")
        XCTAssertEqual(enrollment.entries[0].number, "GTCNEURO")
        XCTAssertEqual(enrollment.entries[0].title, "Neural Data Science")
        XCTAssertEqual(enrollment.entries[0].status, "storniert")
        XCTAssertTrue(enrollment.entries[0].scheduleText?.contains("jeden Mittwoch") == true)

        let exam = enrollment.entries[1]
        XCTAssertEqual(exam.category, "Prüfung")
        XCTAssertEqual(exam.eventType, "Prüfung")
        XCTAssertEqual(exam.number, "INFO-THEO-1-9CP")
        XCTAssertEqual(exam.title, "Probabilistic Machine Learning")
        XCTAssertEqual(exam.status, "zugelassen")
        XCTAssertEqual(exam.semester, "SoSe 2026")
        XCTAssertEqual(exam.attempt, "1")
        XCTAssertTrue(exam.scheduleText?.contains("Donnerstag 23.07.26") == true)
        XCTAssertTrue(exam.scheduleText?.contains("Prüfungsform: Schriftlich oder mündlich") == true)
        XCTAssertEqual(exam.detailURL, "/alma/pages/startFlow.xhtml?_flowId=detailView-flow&unitId=63233")
    }

    func testParsesExamOverviewRows() throws {
        let html = """
        <table class="treeTableWithIcons">
          <tr class="treeTableCellLevel2">
            <td><img class="submitImageTable" alt="Module"></td>
            <td><span id="examsReadonly:0:defaulttext">Algorithms</span></td>
            <td><span id="examsReadonly:0:elementnr">INF-101</span></td>
            <td><span id="examsReadonly:0:attempt">1</span></td>
            <td><span id="examsReadonly:0:grade">1,3</span></td>
            <td><span id="examsReadonly:0:bonus">6,0</span></td>
            <td><span id="examsReadonly:0:malus"></span></td>
            <td><span id="examsReadonly:0:workstatus">BE</span></td>
            <td><span id="examsReadonly:0:remark"></span></td>
            <td><span id="examsReadonly:0:release"></span></td>
          </tr>
        </table>
        """

        let exams = try AlmaAcademicHTMLParser.parseExamOverview(html, limit: 10)

        XCTAssertEqual(exams.count, 1)
        XCTAssertEqual(exams[0].level, 2)
        XCTAssertEqual(exams[0].kind, "Module")
        XCTAssertEqual(exams[0].title, "Algorithms")
        XCTAssertEqual(exams[0].number, "INF-101")
        XCTAssertEqual(exams[0].attempt, "1")
        XCTAssertEqual(exams[0].grade, "1,3")
        XCTAssertEqual(exams[0].cp, "6,0")
        XCTAssertEqual(exams[0].status, "BE")
    }

    func testParsesExamRowsWhenTreeTableClassIsMissing() throws {
        let html = """
        <form id="examsReadonly">
          <table id="examsReadonly:tree">
            <tbody>
              <tr>
                <td class="treeTableCellLevel3"><img class="submitImageTable" alt="Konto"></td>
                <td><span id = "examsReadonly:0:unDeftxt">Studienbegleitende Leistungen</span></td>
                <td><span id="examsReadonly:0:elementnr">9055</span></td>
                <td><span id="examsReadonly:0:attempt">1</span></td>
                <td><span id="examsReadonly:0:grade">1,0</span></td>
                <td><span id="examsReadonly:0:bonus">9</span></td>
                <td><span id="examsReadonly:0:malus">0</span></td>
                <td><span id="examsReadonly:0:workstatus">BE</span></td>
                <td><span id="examsReadonly:0:remark"></span></td>
                <td><span id="examsReadonly:0:release"></span></td>
              </tr>
            </tbody>
          </table>
        </form>
        """

        let exams = try AlmaAcademicHTMLParser.parseExamOverview(html, limit: 10)

        XCTAssertEqual(exams.count, 1)
        XCTAssertEqual(exams[0].level, 3)
        XCTAssertEqual(exams[0].kind, "Konto")
        XCTAssertEqual(exams[0].title, "Studienbegleitende Leistungen")
        XCTAssertEqual(exams[0].number, "9055")
        XCTAssertEqual(exams[0].grade, "1,0")
        XCTAssertEqual(exams[0].cp, "9")
        XCTAssertEqual(exams[0].status, "BE")
    }
}
