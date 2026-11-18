import XCTest
@testable import TueAPI

final class LectureWidgetScheduleTests: XCTestCase {
    func testUpcomingUsesEntryDateAndExcludesCancellations() {
        let now = Date(timeIntervalSince1970: 1_000)
        let current = lecture("current", start: now, end: now.addingTimeInterval(60))
        let later = lecture("later", start: now.addingTimeInterval(300), end: nil)
        var cancelled = lecture("cancelled", start: now, end: now.addingTimeInterval(120))
        cancelled.status = .cancelled
        let events = [later, cancelled, current]

        XCTAssertEqual(LectureWidgetSchedule.upcoming(events, at: now).map(\.id), ["current", "later"])
        XCTAssertEqual(LectureWidgetSchedule.upcoming(events, at: now.addingTimeInterval(61)).map(\.id), ["later"])
        XCTAssertEqual(LectureWidgetSchedule.entryDates(events, from: now, until: now.addingTimeInterval(180)), [now, now.addingTimeInterval(61)])
    }

    private func lecture(_ id: String, start: Date, end: Date?) -> LectureEvent {
        LectureEvent(id: id, title: id, startDate: start, endDate: end)
    }
}
