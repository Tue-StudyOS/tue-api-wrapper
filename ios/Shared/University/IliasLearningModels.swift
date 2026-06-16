import Foundation

struct IliasContentItem: Codable, Equatable, Identifiable {
    var label: String
    var url: String
    var kind: String?
    var properties: [String]

    var id: String { url }
}

struct IliasContentSection: Codable, Equatable, Identifiable {
    var label: String
    var items: [IliasContentItem]

    var id: String { label }
}

struct IliasContentPage: Codable, Equatable {
    var title: String
    var pageURL: String
    var sections: [IliasContentSection]

    enum CodingKeys: String, CodingKey {
        case title, sections
        case pageURL = "page_url"
    }
}

struct IliasExerciseAssignment: Codable, Equatable, Identifiable {
    var title: String
    var url: String
    var dueHint: String?
    var dueAt: String?
    var requirement: String?
    var lastSubmission: String?
    var submissionType: String?
    var status: String?
    var teamActionURL: String?

    var id: String { url }

    enum CodingKeys: String, CodingKey {
        case title, url, requirement, status
        case dueHint = "due_hint"
        case dueAt = "due_at"
        case lastSubmission = "last_submission"
        case submissionType = "submission_type"
        case teamActionURL = "team_action_url"
    }
}

struct IliasCourseExerciseAssignments: Codable, Equatable, Identifiable {
    var exercise: IliasContentItem
    var assignments: [IliasExerciseAssignment]

    var id: String { exercise.id }
}

struct IliasCourseAssignmentsPage: Codable, Equatable {
    var course: IliasContentPage
    var exercises: [IliasCourseExerciseAssignments]
}
