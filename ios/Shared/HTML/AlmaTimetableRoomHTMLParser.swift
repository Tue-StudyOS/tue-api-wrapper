import Foundation

struct AlmaTimetableRoomEntry: Hashable {
    var summary: String
    var weekday: Int?
    var startTime: String?
    var endTime: String?
    var startDate: Date?
    var endDate: Date?
    var roomDetails: LectureRoomDetails
}

enum AlmaTimetableRoomHTMLParser {
    static func entries(from html: String, pageURL: URL) -> [AlmaTimetableRoomEntry] {
        panelBlocks(in: html).compactMap { panel in
            guard let summary = textForTag("h3", className: "scheduleTitle", in: panel) else {
                return nil
            }
            let details = roomDetails(in: panel, pageURL: pageURL)
            guard details.displayText != nil else {
                return nil
            }
            let times = timeRange(fieldText("processingTimes", in: panel))
            return AlmaTimetableRoomEntry(
                summary: summary,
                weekday: weekday(fieldText("weekdayDefaulttext", in: panel)),
                startTime: times.start,
                endTime: times.end,
                startDate: date(fieldText("scheduleStartDate", in: panel)),
                endDate: date(fieldText("scheduleEndDate", in: panel)),
                roomDetails: details
            )
        }
    }

    static func enrich(_ lectures: [LectureEvent], html: String, pageURL: URL) -> [LectureEvent] {
        let roomEntries = entries(from: html, pageURL: pageURL)
        guard !roomEntries.isEmpty else {
            return lectures
        }
        return lectures.map { lecture in
            guard let entry = matchingEntry(for: lecture, entries: roomEntries) else {
                return lecture
            }
            var enriched = lecture
            enriched.roomDetails = entry.roomDetails
            enriched.location = entry.roomDetails.displayText ?? lecture.location
            return enriched
        }
    }

    private static func roomDetails(in panel: String, pageURL: URL) -> LectureRoomDetails {
        var details = LectureRoomDetails(
            roomDefault: fieldText("roomDefaulttext", in: panel),
            roomShort: fieldText("roomShorttext", in: panel),
            roomLong: fieldText("roomLongtext", in: panel),
            floorDefault: fieldText("floorDefaulttext", in: panel),
            floorShort: fieldText("floorShorttext", in: panel),
            floorLong: fieldText("floorLongtext", in: panel),
            buildingDefault: fieldText("buildingDefaulttext", in: panel),
            buildingShort: fieldText("buildingShorttext", in: panel),
            buildingLong: fieldText("buildingLongtext", in: panel),
            campusDefault: fieldText("campusDefaulttext", in: panel),
            campusShort: fieldText("campusShorttext", in: panel),
            campusLong: fieldText("campusLongtext", in: panel),
            detailURL: roomDetailURL(in: panel, pageURL: pageURL),
            displayText: nil
        )
        details.displayText = displayText(for: details)
        return details
    }

    private static func matchingEntry(
        for lecture: LectureEvent,
        entries: [AlmaTimetableRoomEntry]
    ) -> AlmaTimetableRoomEntry? {
        let summaryKey = key(lecture.title)
        let startDay = calendar.startOfDay(for: lecture.startDate)
        let weekday = calendar.component(.weekday, from: lecture.startDate)
        let startTime = timeText(lecture.startDate)
        let endTime = lecture.endDate.map(timeText)

        return entries.first { entry in
            guard key(entry.summary) == summaryKey else { return false }
            if let entryWeekday = entry.weekday, entryWeekday != weekday { return false }
            if let entryStart = entry.startTime, entryStart != startTime { return false }
            if let entryEnd = entry.endTime, let endTime, entryEnd != endTime { return false }
            if let firstDay = entry.startDate, startDay < firstDay { return false }
            if let lastDay = entry.endDate, startDay > lastDay { return false }
            return true
        }
    }

    private static func fieldText(_ token: String, in panel: String) -> String? {
        let escaped = NSRegularExpression.escapedPattern(for: token)
        let pattern = "<([A-Za-z0-9]+)\\b[^>]*\\bid\\s*=\\s*(['\"])[^'\"]*:\(escaped)(?::[^'\"]*)?\\2[^>]*>(.*?)</\\1>"
        return HTMLRegex.firstCapture(pattern, in: panel, group: 3).map(HTMLText.stripTags)?.nilIfBlank
    }

    private static func roomDetailURL(in panel: String, pageURL: URL) -> URL? {
        for token in ["roomDefaulttext", "roomShorttext", "roomLongtext"] {
            let escaped = NSRegularExpression.escapedPattern(for: token)
            let pattern = "<a\\b[^>]*\\bid\\s*=\\s*(['\"])[^'\"]*:\(escaped):showRoomDetailLink[^'\"]*\\1[^>]*>"
            for match in HTMLRegex.matches(pattern, in: panel) {
                guard let range = Range(match.range, in: panel) else {
                    continue
                }
                let tag = String(panel[range])
                if let href = HTMLRegex.attribute("href", in: tag) {
                    return URL(string: href, relativeTo: pageURL)?.absoluteURL
                }
            }
        }
        return nil
    }

    private static func displayText(for details: LectureRoomDetails) -> String? {
        let candidates: [String?] = [
            details.roomDefault ?? details.roomShort ?? details.roomLong,
            details.floorDefault ?? details.floorShort ?? details.floorLong,
            details.buildingDefault ?? details.buildingShort ?? details.buildingLong,
            details.campusDefault ?? details.campusLong ?? details.campusShort
        ]

        var parts: [String] = []
        var seen = Set<String>()

        for candidate in candidates {
            guard let value = candidate?.nilIfBlank else { continue }
            let compactKey = key(value)
            guard !compactKey.isEmpty, !seen.contains(compactKey) else { continue }
            parts.append(value)
            seen.insert(compactKey)
        }

        return parts.joined(separator: ", ").nilIfBlank
    }

    private static func panelBlocks(in html: String) -> [String] {
        let pattern = "<div\\b[^>]*\\bid\\s*=\\s*(['\"])[^'\"]*:scheduleItem:schedulePanelGroup[^'\"]*\\1[^>]*>"
        return HTMLRegex.matches(pattern, in: html).compactMap { match in
            guard let openingRange = Range(match.range, in: html) else {
                return nil
            }
            return balancedDivBlock(in: html, openingRange: openingRange)
        }
    }

    private static func balancedDivBlock(
        in html: String,
        openingRange: Range<String.Index>
    ) -> String? {
        let tail = String(html[openingRange.upperBound...])
        var depth = 1
        for match in HTMLRegex.matches("</div\\s*>|<div\\b[^>]*>", in: tail) {
            guard let tagRange = Range(match.range, in: tail) else {
                continue
            }
            let tag = String(tail[tagRange]).lowercased()
            depth += tag.hasPrefix("</") ? -1 : 1
            guard depth == 0 else {
                continue
            }
            let distance = tail.distance(from: tail.startIndex, to: tagRange.upperBound)
            guard let end = html.index(openingRange.upperBound, offsetBy: distance, limitedBy: html.endIndex) else {
                return nil
            }
            return String(html[openingRange.lowerBound..<end])
        }
        return nil
    }

    private static func textForTag(_ tag: String, className: String, in panel: String) -> String? {
        let escapedTag = NSRegularExpression.escapedPattern(for: tag)
        let escapedClass = NSRegularExpression.escapedPattern(for: className)
        let pattern = "<\(escapedTag)\\b[^>]*\\bclass\\s*=\\s*(['\"])[^'\"]*\\b\(escapedClass)\\b[^'\"]*\\1[^>]*>(.*?)</\(escapedTag)>"
        return HTMLRegex.firstCapture(pattern, in: panel, group: 2).map(HTMLText.stripTags)?.nilIfBlank
    }

    private static func timeRange(_ value: String?) -> (start: String?, end: String?) {
        guard let value else {
            return (nil, nil)
        }
        let pattern = "(\\d{1,2}:\\d{2})\\s*bis\\s*(\\d{1,2}:\\d{2})"
        guard let match = HTMLRegex.matches(pattern, in: value).first,
              let startRange = Range(match.range(at: 1), in: value),
              let endRange = Range(match.range(at: 2), in: value) else {
            return (nil, nil)
        }
        return (normalizeTime(String(value[startRange])), normalizeTime(String(value[endRange])))
    }

    private static func normalizeTime(_ value: String) -> String {
        let parts = value.split(separator: ":", maxSplits: 1).map(String.init)
        guard parts.count == 2, let hour = Int(parts[0]), let minute = Int(parts[1]) else {
            return value
        }
        return String(format: "%02d:%02d", hour, minute)
    }

    private static func date(_ value: String?) -> Date? {
        guard let value = value?.nilIfBlank else {
            return nil
        }
        return dateFormatter.date(from: value).map { calendar.startOfDay(for: $0) }
    }

    private static func weekday(_ value: String?) -> Int? {
        switch key(value ?? "") {
        case "sonntag": 1
        case "montag": 2
        case "dienstag": 3
        case "mittwoch": 4
        case "donnerstag": 5
        case "freitag": 6
        case "samstag": 7
        default: nil
        }
    }

    private static func timeText(_ date: Date) -> String {
        let components = calendar.dateComponents([.hour, .minute], from: date)
        return String(format: "%02d:%02d", components.hour ?? 0, components.minute ?? 0)
    }

    private static func key(_ value: String) -> String {
        value
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
    }

    private static let calendar: Calendar = {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Europe/Berlin") ?? .current
        return calendar
    }()

    private static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "de_DE_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "dd.MM.yyyy"
        return formatter
    }()
}

private extension String {
    var nilIfBlank: String? {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
