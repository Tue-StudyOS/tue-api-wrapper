import Foundation

protocol UniversityCredentialsLoading {
    func load() throws -> AlmaCredentials?
}

protocol UniversityIliasTaskLoading {
    func fetchTasks(limit: Int) async throws -> [IliasTask]
    func fetchAssignmentDeadlines(courseLimit: Int, assignmentLimit: Int) async throws -> [IliasAssignmentDeadline]
}

protocol UniversityMoodleDeadlineLoading {
    func fetchDeadlines(days: Int, limit: Int) async throws -> [MoodleDeadline]
}

struct UniversityTaskSnapshot: Codable {
    var tasks: [IliasTask]
    var iliasAssignments: [IliasAssignmentDeadline]
    var deadlines: [MoodleDeadline]
    var refreshedAt: Date
    var warnings: [String] = []

    var warningMessage: String? {
        let message = warnings.joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        return message.isEmpty ? nil : message
    }
}
