import XCTest
@testable import TueAPI

final class UniversityDirectoryHTMLParserTests: XCTestCase {
    func testMaintenanceRedirectReportsServiceOutage() throws {
        let pageURL = try XCTUnwrap(URL(string: "https://epv-welt.uni-tuebingen.de/Maintenance.aspx"))
        let html = "<form><h1>Wartungsarbeiten</h1><input type='hidden' name='__VIEWSTATE'></form>"
        let expected = UniversityPortalError.portal("The university directory is temporarily unavailable for maintenance. Try again later.")

        XCTAssertThrowsError(try UniversityDirectoryHTMLParser.searchForm(in: html, pageURL: pageURL)) {
            XCTAssertEqual($0 as? UniversityPortalError, expected)
        }
        XCTAssertThrowsError(try UniversityDirectoryHTMLParser.searchResponse(from: html, query: "Informatik", pageURL: pageURL)) {
            XCTAssertEqual($0 as? UniversityPortalError, expected)
        }
    }

    func testSearchFormExtractsQueryableFields() throws {
        let pageURL = URL(string: "https://epv-welt.uni-tuebingen.de/RestrictedPages/StartSearch.aspx")!
        let html = """
        <form method="post" action="./StartSearch.aspx">
          <input type="hidden" name="__VIEWSTATE" value="abc" />
          <input type="text" name="ctl00$MainContent$SearchControl$NameTextBox" value="" />
          <input type="submit" name="ctl00$MainContent$SearchControl$SearchButton" value="Suchen" />
          <input type="submit" name="ctl00$MainContent$SearchControl$NewSearchButton" value="Neue Suche" />
        </form>
        """

        let form = try UniversityDirectoryHTMLParser.searchForm(in: html, pageURL: pageURL)
        let request = form.request(for: "Bernd Engler")

        XCTAssertEqual(request.actionURL.absoluteString, pageURL.absoluteString)
        XCTAssertTrue(request.payload.contains { $0.0 == "__VIEWSTATE" && $0.1 == "abc" })
        XCTAssertTrue(request.payload.contains { $0.0 == "ctl00$MainContent$SearchControl$NameTextBox" && $0.1 == "Bernd Engler" })
        XCTAssertTrue(request.payload.contains { $0.0 == "ctl00$MainContent$SearchControl$SearchButton" && $0.1 == "Suchen" })
    }

    func testSearchResponseBuildsPersonSections() throws {
        let pageURL = URL(string: "https://epv-welt.uni-tuebingen.de/RestrictedPages/SearchResultPersons.aspx")!
        let html = """
        <div id="content">
          <h1>Personen (Fachbereich Informatik)</h1>
          <h2>Professoren</h2>
          <ul>
            <li><a href="javascript:__doPostBack('ctl00$MainContent$ctl01$ctl01','')">Abebe, Rediet, Prof. Dr.</a><span> (Fachbereich Informatik)</span></li>
          </ul>
          <h2>Beschäftigte der Universität</h2>
          <ul>
            <li><a href="javascript:__doPostBack('ctl00$MainContent$ctl01$ctl02','')">Miller, Ada</a><span> (Mathematik)</span></li>
          </ul>
          <h1>Suche</h1>
        </div>
        <form action="./SearchResultPersons.aspx">
          <input type="hidden" name="__VIEWSTATE" value="xyz" />
        </form>
        """

        let response = try UniversityDirectoryHTMLParser.searchResponse(from: html, query: "Informatik", pageURL: pageURL)
        guard case .people(let page) = response.outcome else {
            return XCTFail("Expected people page")
        }

        XCTAssertEqual(response.title, "Personen (Fachbereich Informatik)")
        XCTAssertEqual(page.sections.count, 2)
        XCTAssertEqual(page.sections[0].title, "Professoren")
        XCTAssertEqual(page.sections[0].items[0].name, "Abebe, Rediet, Prof. Dr.")
        XCTAssertEqual(page.sections[0].items[0].subtitle, "Fachbereich Informatik")
        XCTAssertEqual(page.sections[1].items[0].action, .eventTarget("ctl00$MainContent$ctl01$ctl02"))
        XCTAssertTrue(page.form.payload.contains { $0.0 == "__VIEWSTATE" && $0.1 == "xyz" })
    }

    func testSearchResponseBuildsSinglePersonDetail() throws {
        let pageURL = URL(string: "https://epv-welt.uni-tuebingen.de/RestrictedPages/SinglePerson.aspx")!
        let html = """
        <div id="content">
          <h1>Bernd Engler</h1>
          <h3>Englisches Seminar</h3>
          <table>
            <tr><td>Anrede</td><td>Herr</td></tr>
            <tr><td>E-Mail</td><td>bernd.engler<img src="../Images/AtSign.gif" alt="At" />uni-tuebingen.de</td></tr>
            <tr><td>Dienststelle</td><td>Philosophische Fakultät<br />Englisches Seminar</td></tr>
          </table>
          <div class="cp_title"><span>Kontaktdaten des Büros: Englisches Seminar</span></div>
          <div class="cp_content">
            <table>
              <tr><td>Telefon</td><td>+49 7071 29-72959</td></tr>
            </table>
          </div>
          <div id="nextSearch"></div>
        </div>
        <form action="./SinglePerson.aspx">
          <input type="hidden" name="__VIEWSTATE" value="abc" />
        </form>
        """

        let response = try UniversityDirectoryHTMLParser.searchResponse(from: html, query: "Bernd Engler", pageURL: pageURL)
        guard case .person(let person) = response.outcome else {
            return XCTFail("Expected single person")
        }

        XCTAssertEqual(person.name, "Bernd Engler")
        XCTAssertEqual(person.summary, "Englisches Seminar")
        XCTAssertEqual(person.attributes[1].value, "bernd.engler@uni-tuebingen.de")
        XCTAssertEqual(person.attributes[2].value, "Philosophische Fakultät\nEnglisches Seminar")
        XCTAssertEqual(person.contactSections[0].title, "Kontaktdaten des Büros: Englisches Seminar")
        XCTAssertEqual(person.contactSections[0].fields[0].value, "+49 7071 29-72959")
    }

    func testSearchResponseBuildsSingleOrganizationWithPersonListAction() throws {
        let pageURL = URL(string: "https://epv-welt.uni-tuebingen.de/RestrictedPages/SingleOrganization.aspx")!
        let html = """
        <div id="content">
          <h1>Fachbereich Informatik</h1>
          <table>
            <tr><td>Anschrift</td><td>Sand 14<br />72076 Tübingen</td></tr>
            <tr><td>Web</td><td>https://uni-tuebingen.de</td></tr>
          </table>
          <input type="submit" name="ctl00$MainContent$PersonListButton" value="Personenliste" />
          <div id="nextSearch"></div>
        </div>
        <form action="./SingleOrganization.aspx">
          <input type="hidden" name="__VIEWSTATE" value="org" />
        </form>
        """

        let response = try UniversityDirectoryHTMLParser.searchResponse(from: html, query: "Informatik", pageURL: pageURL)
        guard case .organization(let organization) = response.outcome else {
            return XCTFail("Expected single organization")
        }

        XCTAssertEqual(organization.name, "Fachbereich Informatik")
        XCTAssertEqual(organization.fields[0].value, "Sand 14\n72076 Tübingen")
        XCTAssertEqual(
            organization.personListAction,
            .submit(name: "ctl00$MainContent$PersonListButton", value: "Personenliste")
        )
        XCTAssertTrue(organization.form.payload.contains { $0.0 == "__VIEWSTATE" && $0.1 == "org" })
    }
}
