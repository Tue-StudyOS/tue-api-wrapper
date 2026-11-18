import Foundation

enum AlmaTimetableCancellationHTMLParser {
    private static let dayHeading = #"<div\b[^>]*class\s*=\s*['"][^'"]*\bcolhead\b[^'"]*['"][^>]*>\s*<h2\b[^>]*>(.*?)</h2>"#
    private static let cancelledBlock = #"<li\b[^>]*class\s*=\s*['"][^'"]*\bscheduleCancelled\b[^'"]*['"][^>]*>(.*?)</li>"#

    static func visibleDays(in html: String) -> [Date] {
        let formatter = dateFormatter("dd.MM.yyyy")
        return HTMLRegex.matches(dayHeading, in: html).compactMap { match in
            guard let range = Range(match.range(at: 1), in: html),
                  let day = dayText(in: String(html[range])) else { return nil }
            return formatter.date(from: day)
        }
    }

    static func merge(_ lectures: [LectureEvent], with cancellations: [LectureEvent]) -> [LectureEvent] {
        guard !cancellations.isEmpty else { return lectures }
        var bySlot = Dictionary(cancellations.map { (Slot(event: $0), $0) }, uniquingKeysWith: { first, _ in first })
        var result = lectures.map { lecture in
            guard let cancellation = bySlot.removeValue(forKey: Slot(event: lecture)) else { return lecture }
            var updated = lecture
            updated.status = cancellation.status
            updated.cancellationReason = cancellation.cancellationReason
            return updated
        }
        result.append(contentsOf: bySlot.values)
        return result.sorted {
            $0.startDate == $1.startDate ? $0.title.localizedCaseInsensitiveCompare($1.title) == .orderedAscending
                : $0.startDate < $1.startDate
        }
    }

    static func cancellations(in html: String) -> [LectureEvent] {
        let formatter = dateFormatter("dd.MM.yyyy HH:mm")
        var headingDate: String?
        var events: [LectureEvent] = []
        for match in HTMLRegex.matches(dayHeading + "|" + cancelledBlock, in: html) {
            if let heading = Range(match.range(at: 1), in: html) {
                headingDate = dayText(in: String(html[heading]))
            } else if let headingDate, let block = Range(match.range(at: 2), in: html),
                      let event = cancellation(in: String(html[block]), on: headingDate, formatter: formatter) {
                events.append(event)
            }
        }
        return events
    }

    private static func cancellation(in block: String, on day: String, formatter: DateFormatter) -> LectureEvent? {
        let parser = AlmaTimetableRoomHTMLParser.self
        let times = parser.timeRange(parser.fieldText("processingTimes", in: block))
        guard let title = parser.textForTag("h3", className: "scheduleTitle", in: block),
              let start = times.start, let end = times.end,
              let startDate = formatter.date(from: "\(day) \(start)"),
              let endDate = formatter.date(from: "\(day) \(end)") else {
            return nil
        }
        return LectureEvent(
            id: "alma-cancelled-\(title)-\(Int(startDate.timeIntervalSince1970))-\(end)",
            title: title,
            startDate: startDate,
            endDate: endDate,
            status: .cancelled,
            cancellationReason: reason(in: block)
        )
    }

    private static func reason(in block: String) -> String? {
        let pattern = #"<div\b[^>]*class\s*=\s*['"][^'"]*\berrortextPlan\b[^'"]*['"][^>]*>"#
        let parser = AlmaTimetableRoomHTMLParser.self
        guard let match = HTMLRegex.matches(pattern, in: block).first,
              let opening = Range(match.range, in: block),
              let warning = parser.balancedDivBlock(in: block, openingRange: opening) else {
            return nil
        }
        return parser.textForTag("div", className: "fieldsetMessageText", in: warning)
    }

    private static func dayText(in heading: String) -> String? {
        HTMLRegex.firstCapture(#"(\d{2}\.\d{2}\.\d{4})"#, in: heading)
    }

    static func dateFormatter(_ format: String) -> DateFormatter {
        let formatter = DateFormatter()
        formatter.calendar = ICSDateParser.calendar()
        formatter.locale = Locale(identifier: "de_DE_POSIX")
        formatter.timeZone = ICSDateParser.berlinTimeZone
        formatter.dateFormat = format
        return formatter
    }

    private struct Slot: Hashable {
        let title: String
        let start: Date
        let end: Date?

        init(event: LectureEvent) {
            title = event.title.split(whereSeparator: \.isWhitespace).joined(separator: " ").lowercased()
            start = event.startDate
            end = event.endDate
        }
    }
}
