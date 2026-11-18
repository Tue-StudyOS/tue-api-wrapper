import Foundation

enum LectureEventStatus: String, Codable {
    case cancelled
}

struct LectureEvent: Codable, Identifiable, Hashable {
    var id: String
    var title: String
    var startDate: Date
    var endDate: Date?
    var location: String?
    var detail: String?
    var roomDetails: LectureRoomDetails? = nil
    var status: LectureEventStatus? = nil
    var cancellationReason: String? = nil

    var isCancelled: Bool { status == .cancelled }

    var timeRangeText: String {
        guard let endDate else {
            return Self.startFormatter.string(from: startDate)
        }
        return "\(Self.startFormatter.string(from: startDate)) – \(Self.endFormatter.string(from: endDate))"
    }

    // MARK: - Shared formatters (allocated once)

    private static let berlinZone = TimeZone(identifier: "Europe/Berlin") ?? .current

    private static let startFormatter: DateFormatter = {
        let f = DateFormatter()
        f.timeZone = berlinZone
        f.dateFormat = "E, dd.MM. HH:mm"
        return f
    }()

    private static let endFormatter: DateFormatter = {
        let f = DateFormatter()
        f.timeZone = berlinZone
        f.dateFormat = "HH:mm"
        return f
    }()

    // MARK: - Placeholder for skeleton loading

    static let placeholder = LectureEvent(
        id: "placeholder",
        title: "Introduction to Computer Science",
        startDate: Date(),
        endDate: Date().addingTimeInterval(5400),
        location: "Sand 14, Room 0.01"
    )
}

struct LectureSnapshot: Codable, Equatable {
    var refreshedAt: Date
    var sourceTerm: String
    var events: [LectureEvent]
    var semesterCredits: SemesterCreditSummary?
    var personName: String?
}

struct SemesterCreditSummary: Codable, Equatable {
    var totalCredits: Double
    var resolvedCourseCount: Int
    var unresolvedCourseCount: Int
    var unresolvedCourseTitles: [String]

    var isComplete: Bool {
        unresolvedCourseCount == 0
    }

    var displayText: String {
        let credits = totalCredits.rounded() == totalCredits ? String(Int(totalCredits)) : String(format: "%.1f", totalCredits)
        if unresolvedCourseCount > 0 {
            return "\(credits) CP resolved, \(unresolvedCourseCount) courses missing CP"
        }
        return "\(credits) CP saved semester"
    }
}

enum SemesterCreditCounter {
    private static let creditRegex = try? NSRegularExpression(
        pattern: #"(?i)(?:^|[^0-9])(\d{1,2}(?:[,.]\d{1,2})?)\s*(?:CP|LP|ECTS)\b"#
    )

    static func summarize(_ events: [AlmaCalendarEvent]) -> SemesterCreditSummary {
        let titles = Set(events.map(\.summary).filter { !$0.isEmpty })
        var creditsByTitle: [String: Double] = [:]

        for event in events {
            guard creditsByTitle[event.summary] == nil,
                  let credits = parseCredits(from: event.detail ?? "") else {
                continue
            }
            creditsByTitle[event.summary] = credits
        }

        let unresolved = titles
            .filter { creditsByTitle[$0] == nil }
            .sorted { $0.localizedCaseInsensitiveCompare($1) == .orderedAscending }

        return SemesterCreditSummary(
            totalCredits: creditsByTitle.values.reduce(0, +),
            resolvedCourseCount: creditsByTitle.count,
            unresolvedCourseCount: unresolved.count,
            unresolvedCourseTitles: unresolved
        )
    }

    private static func parseCredits(from text: String) -> Double? {
        guard let creditRegex else {
            return nil
        }
        let fullRange = NSRange(text.startIndex..<text.endIndex, in: text)
        guard let match = creditRegex.firstMatch(in: text, range: fullRange),
              match.numberOfRanges > 1,
              let valueRange = Range(match.range(at: 1), in: text),
              let value = Double(text[valueRange].replacingOccurrences(of: ",", with: ".")) else {
            return nil
        }
        return value
    }
}
