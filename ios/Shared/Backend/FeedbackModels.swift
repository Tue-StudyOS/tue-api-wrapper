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

struct AppFeedbackIssueDraft: Equatable {
    var issueURL: URL
    var title: String
}

extension AppFeedbackIssueRequest {
    var githubIssueDraft: AppFeedbackIssueDraft {
        let title = "[iOS Feedback] \(category.title): \(self.title)"
        var components = URLComponents(string: "https://github.com/SebastianBoehler/tue-api-wrapper/issues/new")!
        components.queryItems = [
            URLQueryItem(name: "title", value: title),
            URLQueryItem(name: "body", value: githubBody),
            URLQueryItem(name: "labels", value: "feedback")
        ]
        return AppFeedbackIssueDraft(issueURL: components.url!, title: title)
    }

    private var githubBody: String {
        var parts = [
            "<!-- source: tue-api-ios-feedback -->",
            "<!-- platform: ios -->",
            "## Summary",
            summary,
            "## Context",
            "- Category: \(category.title)",
            "- Area: \(area ?? "Not specified")",
            "- App version: \(appVersion) (\(buildNumber))",
            "- OS version: \(systemVersion)",
            "- Device: \(deviceModel)",
            "- Submitted at: \(ISO8601DateFormatter().string(from: Date()))"
        ]

        if let reproductionSteps {
            parts.append(contentsOf: ["## Reproduction Steps", reproductionSteps])
        }
        if let expectedBehavior {
            parts.append(contentsOf: ["## Expected Behavior", expectedBehavior])
        }

        parts.append(contentsOf: [
            "## Notes",
            "- Submitted from the iOS in-app feedback sheet.",
            "- Avoid posting personal data, credentials, or student records in follow-up comments."
        ])

        return parts.joined(separator: "\n\n")
    }
}
