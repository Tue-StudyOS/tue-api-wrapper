import XCTest
@testable import TueAPI

final class AlmaTimetableRoomHTMLParserTests: XCTestCase {
    func testParsesDetailedRoomFields() throws {
        let entries = AlmaTimetableRoomHTMLParser.entries(
            from: Self.roomDetailHTML,
            pageURL: URL(string: "https://alma.example/alma/pages/plan/individualTimetable.xhtml")!
        )

        let entry = try XCTUnwrap(entries.first)
        XCTAssertEqual(entry.summary, "INFO4195b AI for Scientific Discovery")
        XCTAssertEqual(entry.weekday, 4)
        XCTAssertEqual(entry.startTime, "18:00")
        XCTAssertEqual(entry.endTime, "20:00")
        XCTAssertEqual(entry.roomDetails.floorDefault, "EG")
        XCTAssertEqual(entry.roomDetails.buildingDefault, "Cyber Valley Campus, MVL1")
        XCTAssertEqual(entry.roomDetails.campusDefault, "Morgenstelle")
        XCTAssertEqual(
            entry.roomDetails.displayText,
            "Hörsaal A1 (A-206), EG, Cyber Valley Campus, MVL1, Morgenstelle"
        )
        XCTAssertEqual(
            entry.roomDetails.detailURL?.absoluteString,
            "https://alma.example/alma/pages/cm/exa/searchRoomDetail.xhtml?roomId=470"
        )
    }

    func testEnrichesLectureEventsWithDetailedRoomFields() throws {
        let lecture = LectureEvent(
            id: "ai-20260422",
            title: "INFO4195b AI for Scientific Discovery",
            startDate: try Self.date("2026-04-22 18:00"),
            endDate: try Self.date("2026-04-22 20:00"),
            location: "Hörsaal A1 (A-206) Cyber Valley Campus, MVL1"
        )

        let enriched = AlmaTimetableRoomHTMLParser.enrich(
            [lecture],
            html: Self.roomDetailHTML,
            pageURL: URL(string: "https://alma.example/alma/pages/plan/individualTimetable.xhtml")!
        )

        XCTAssertEqual(
            enriched.first?.location,
            "Hörsaal A1 (A-206), EG, Cyber Valley Campus, MVL1, Morgenstelle"
        )
        XCTAssertEqual(enriched.first?.roomDetails?.floorDefault, "EG")
    }

    func testRestoresOnlyTheDatedCancelledOccurrence() throws {
        let html = """
        <div class="colhead"><h2>Mi., 18.11.2026</h2></div>
        <li class="singleblock scheduleCancelled planelementchange">
          <div class="errortextPlan">
            <div class="fieldsetMessageText infoBox">Studieninfotag</div>
          </div>
          <h3 class="scheduleTitle">ML4103 Deep Learning</h3>
          <span id="plan:schedule:scheduleItem:processingTimes">14:00 bis 16:00</span>
          <span id="plan:schedule:scheduleItem:scheduleStartDate">14.10.2026</span>
        </li>
        """
        let events = try ICSEventParser.parse("""
        BEGIN:VCALENDAR
        BEGIN:VEVENT
        UID:deep-learning-lecture
        SUMMARY:ML4103 Deep Learning
        DTSTART;TZID=Europe/Berlin:20261111T140000
        DTEND;TZID=Europe/Berlin:20261111T160000
        RRULE:FREQ=WEEKLY;UNTIL=20261202T160000
        EXDATE;TZID=Europe/Berlin:20261118T140000,20261202T140000
        END:VEVENT
        END:VCALENDAR
        """)
        let active = try RecurrenceExpander.expand(
            events, from: Self.date("2026-11-18 00:00"), to: Self.date("2026-12-02 23:59")
        )
        let parser = AlmaTimetableCancellationHTMLParser.self
        let merged = parser.merge(active, with: parser.cancellations(in: html))

        XCTAssertEqual(merged.map(\.startDate), [
            try Self.date("2026-11-18 14:00"), try Self.date("2026-11-25 14:00")
        ])
        XCTAssertEqual(merged.first?.endDate, try Self.date("2026-11-18 16:00"))
        XCTAssertEqual(merged.map(\.status), [.cancelled, nil])
        XCTAssertEqual(merged.first?.cancellationReason, "Studieninfotag")
    }

    private static func date(_ value: String) throws -> Date {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Europe/Berlin")
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return try XCTUnwrap(formatter.date(from: value))
    }

    private static let roomDetailHTML = """
    <div class="schedulePanel" id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:schedulePanelGroup">
      <div class="scheduleItemInnerContent">
        <h3 class="scheduleTitle">INFO4195b AI for Scientific Discovery</h3>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:weekdayDefaulttext">Mittwoch</span>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:processingTimes">18:00 bis 20:00</span>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:scheduleStartDate">15.04.2026</span>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:scheduleEndDate">22.07.2026</span>
        <a href="/alma/pages/cm/exa/searchRoomDetail.xhtml?roomId=470"
           id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:roomDefaulttext:showRoomDetailLink">
          <span>Hörsaal A1 (A-206)</span>
        </a>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:floorDefaulttext">EG</span>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:buildingDefaulttext">
          Cyber Valley Campus, MVL1
        </span>
        <span id="plan:schedule:scheduleColumn:0:termin:0:scheduleItem:campusDefaulttext">Morgenstelle</span>
      </div>
    </div>
    """
}
