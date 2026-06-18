import Foundation

// MARK: - Alma Grades

struct AlmaEnrollmentState: Decodable {
    var selectedTerm: String?
    var availableTerms: [String: String]
    var message: String?
    var personName: String?
    var entries: [AlmaEnrollmentRecord]

    init(
        selectedTerm: String?,
        availableTerms: [String: String],
        message: String?,
        personName: String?,
        entries: [AlmaEnrollmentRecord] = []
    ) {
        self.selectedTerm = selectedTerm
        self.availableTerms = availableTerms
        self.message = message
        self.personName = personName
        self.entries = entries
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        selectedTerm = try container.decodeIfPresent(String.self, forKey: .selectedTerm)
        availableTerms = try container.decodeIfPresent([String: String].self, forKey: .availableTerms) ?? [:]
        message = try container.decodeIfPresent(String.self, forKey: .message)
        personName = try container.decodeIfPresent(String.self, forKey: .personName)
        entries = try container.decodeIfPresent([AlmaEnrollmentRecord].self, forKey: .entries) ?? []
    }

    enum CodingKeys: String, CodingKey {
        case entries, message
        case personName = "person_name"
        case selectedTerm = "selected_term"
        case availableTerms = "available_terms"
    }
}

struct AlmaEnrollmentRecord: Decodable, Hashable, Identifiable {
    var category: String?
    var title: String
    var number: String?
    var eventType: String?
    var status: String?
    var semester: String?
    var scheduleText: String?
    var detailURL: String?
    var attempt: String?

    var id: String {
        [
            cleanIDComponent(category),
            cleanIDComponent(number),
            cleanIDComponent(title),
            cleanIDComponent(semester),
            cleanIDComponent(status)
        ]
            .compactMap { $0 }
            .joined(separator: ":")
    }

    enum CodingKeys: String, CodingKey {
        case category, title, number, status, semester, attempt
        case eventType = "event_type"
        case scheduleText = "schedule_text"
        case detailURL = "detail_url"
    }
}

struct AlmaExamRecord: Decodable, Hashable, Identifiable {
    var level: Int
    var kind: String?
    var title: String
    var number: String?
    var attempt: String?
    var grade: String?
    var cp: String?
    var status: String?

    var id: String {
        [
            cleanIDComponent(number),
            cleanIDComponent(title),
            cleanIDComponent(attempt),
            cleanIDComponent(grade),
            cleanIDComponent(status)
        ]
            .compactMap { $0 }
            .joined(separator: ":")
    }
}

// MARK: - Moodle Grades

struct MoodleGradeItem: Decodable, Hashable, Identifiable {
    var courseTitle: String
    var grade: String?
    var percentage: String?
    var rangeHint: String?
    var rank: String?
    var feedback: String?
    var url: String?

    var id: String {
        [
            cleanIDComponent(courseTitle),
            cleanIDComponent(grade),
            cleanIDComponent(percentage),
            cleanIDComponent(url)
        ]
            .compactMap { $0 }
            .joined(separator: ":")
    }

    enum CodingKeys: String, CodingKey {
        case grade, percentage, rank, feedback, url
        case courseTitle = "course_title"
        case rangeHint = "range_hint"
    }
}

private func cleanIDComponent(_ value: String?) -> String? {
    value?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false
        ? value?.trimmingCharacters(in: .whitespacesAndNewlines)
        : nil
}

struct MoodleGradesResponse: Decodable {
    var sourceURL: String
    var items: [MoodleGradeItem]

    enum CodingKeys: String, CodingKey {
        case items
        case sourceURL = "source_url"
    }
}

// MARK: - Grade Overview

struct GradeOverviewPayload {
    var enrollment: AlmaEnrollmentState
    var exams: [AlmaExamRecord]
    var moodleGrades: MoodleGradesResponse
    var refreshedAt: Date
}

enum GradeLoadPhase: Equatable {
    case idle
    case loading
    case loaded(Date)
    case unavailable
    case failed(String)

    var isLoading: Bool {
        if case .loading = self {
            return true
        }
        return false
    }
}
