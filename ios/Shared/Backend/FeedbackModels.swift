import Foundation

enum AppFeedbackCategory: String, CaseIterable, Identifiable, Codable {
    case bug
    case feature
    case improvement
    case other

    var id: String { rawValue }

    var title: String {
        switch self {
        case .bug:
            "Bug"
        case .feature:
            "Feature"
        case .improvement:
            "Improvement"
        case .other:
            "Other"
        }
    }
}

struct AppFeedbackIssueRequest: Codable, Equatable {
    var platform = "ios"
    var category: AppFeedbackCategory
    var title: String
    var summary: String
    var area: String?
    var expectedBehavior: String?
    var reproductionSteps: String?
    var appVersion: String
    var buildNumber: String
    var systemVersion: String
    var deviceModel: String
}

struct AppFeedbackIssueResponse: Decodable, Equatable {
    var issueNumber: Int
    var issueURL: String
    var title: String
}

struct AppFeedbackStatusResponse: Decodable, Equatable {
    var enabled: Bool
    var repository: String?
    var detail: String
}
