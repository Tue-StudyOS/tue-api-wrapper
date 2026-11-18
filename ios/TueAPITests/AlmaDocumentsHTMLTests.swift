import XCTest
@testable import TueAPI

final class AlmaDocumentsHTMLTests: XCTestCase {
    private let page = URL(string: "https://alma.uni-tuebingen.de/alma/start.xhtml")!

    func testStudyServiceFormUsesAlmaReportIdentifiersAndHiddenState() throws {
        let html = """
        <form id="other"><button name="other:job2">Do not show</button></form>
        <form id="studyserviceForm" action="report.xhtml?execution=e1s2&amp;continue=true">
            <input type="hidden" name="javax.faces.ViewState" value="1">
            <input type="password" name="ignore" value="">
            <button name="studyserviceForm:content.documents">Bescheide</button>
            <button name="studyserviceForm:document:job2"><span>Certificate of enrollment</span></button>
        </form>
        """
        let form = try AlmaDocumentForm.parse(html, at: page)
        XCTAssertEqual(form.reports, [
            AlmaDocumentOption(id: "studyserviceForm:document:job2", title: "Certificate of enrollment")
        ])
        XCTAssertEqual(form.documentsTab?.title, "Bescheide")
        XCTAssertEqual(form.fields, ["javax.faces.ViewState": "1"])
        XCTAssertEqual(form.action.absoluteString, "https://alma.uni-tuebingen.de/alma/report.xhtml?execution=e1s2&continue=true")
    }

    func testPartialFormKeepsSemesterChoicesAndPollAction() throws {
        let response = """
        <partial-response><changes><update id="content"><![CDATA[
        <form id="studyserviceForm" action="/alma/job.xhtml">
            <select name="studyserviceForm:setting_0:setting_input">
                <option disabled value="">Choose</option>
                <option value="26" selected>Winter 2026/27</option>
                <option value="25">Summer 2026</option>
            </select>
            <button name="studyserviceForm:startJob">PDF erstellen</button>
            <input type="submit" name="studyserviceForm:jobDownloadPoll:poll" value="">
        </form>
        ]]></update></changes></partial-response>
        """
        let form = try AlmaDocumentForm.parse(response, at: page)
        let termField = try XCTUnwrap(form.termField)
        XCTAssertEqual(form.fields[termField], "26")
        XCTAssertEqual(form.terms.map(\.id), ["26", "25"])
        XCTAssertEqual(form.start?.title, "PDF erstellen")
        XCTAssertEqual(form.poll?.id, "studyserviceForm:jobDownloadPoll:poll")
    }

    func testDownloadLinksRequireAlmaDocumentStateParameter() {
        let html = """
        <a href="/alma/download.xhtml?state=docdownload&amp;id=42">PDF</a>
        <a href="/alma/download.xhtml?other=state%3Ddocdownload">Other</a>
        """
        XCTAssertEqual(AlmaDocumentsHTML.downloadLinks(html, at: page).map(\.absoluteString), [
            "https://alma.uni-tuebingen.de/alma/download.xhtml?state=docdownload&id=42"
        ])
    }
}
