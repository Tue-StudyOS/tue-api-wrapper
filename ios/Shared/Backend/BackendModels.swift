import Foundation

// MARK: - ILIAS Tasks

struct IliasTasksPage: Codable {
    var tasks: [IliasTask]
}

struct IliasTask: Codable, Identifiable {
    var title: String
    var url: String
    var itemType: String?
    var start: String?
    var end: String?

    var id: String { url }

    enum CodingKeys: String, CodingKey {
        case title, url, start, end
        case itemType = "item_type"
    }
}

// MARK: - Moodle Calendar

struct MoodleCalendarResponse: Codable {
    var items: [MoodleDeadline]
    var fromTimestamp: Int
    var toTimestamp: Int

    enum CodingKeys: String, CodingKey {
        case items
        case fromTimestamp = "from_timestamp"
        case toTimestamp = "to_timestamp"
    }
}

struct MoodleDeadline: Codable, Identifiable {
    var rawId: Int?
    var title: String
    var dueAt: String?
    var formattedTime: String?
    var courseName: String?
    var courseId: Int?
    var actionURL: String?
    var isActionable: Bool

    var id: String { rawId.map(String.init) ?? title }

    enum CodingKeys: String, CodingKey {
        case title
        case rawId = "id"
        case dueAt = "due_at"
        case formattedTime = "formatted_time"
        case courseName = "course_name"
        case courseId = "course_id"
        case actionURL = "action_url"
        case isActionable = "is_actionable"
    }
}

// MARK: - Load Phase

enum TasksLoadPhase: Equatable {
    case idle
    case loading
    case loaded(Date)
    case unavailable
    case failed(String)
}
