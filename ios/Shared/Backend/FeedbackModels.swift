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

struct AppFeedbackIssue: Equatable {
    var issueURL: URL
    var title: String
}

extension AppFeedbackIssueRequest {
    var githubTitle: String {
        "[iOS Feedback] \(category.title): \(self.title)"
    }

    var githubBody: String {
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

struct AppFeedbackGitHubClient {
    private let repository = "SebastianBoehler/tue-api-wrapper"
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    static var isConfigured: Bool {
        AppFeedbackConfiguration.githubToken != nil
    }

    func createIssue(_ feedback: AppFeedbackIssueRequest) async throws -> AppFeedbackIssue {
        guard let token = AppFeedbackConfiguration.githubToken else {
            throw AppFeedbackError.notConfigured
        }

        let endpoint = URL(string: "https://api.github.com/repos/\(repository)/issues")!
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("2022-11-28", forHTTPHeaderField: "X-GitHub-Api-Version")
        request.httpBody = try JSONEncoder().encode(GitHubIssueCreateRequest(
            title: feedback.githubTitle,
            body: feedback.githubBody,
            labels: ["feedback"]
        ))

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AppFeedbackError.invalidResponse
        }

        if (200..<300).contains(httpResponse.statusCode),
           let issue = try? JSONDecoder().decode(GitHubIssueCreateResponse.self, from: data),
           let issueURL = URL(string: issue.htmlURL) {
            return AppFeedbackIssue(issueURL: issueURL, title: feedback.githubTitle)
        }

        if let error = try? JSONDecoder().decode(GitHubErrorResponse.self, from: data) {
            throw AppFeedbackError.github(error.message)
        }

        throw AppFeedbackError.github("GitHub issue creation failed.")
    }
}

private enum AppFeedbackConfiguration {
    static var githubToken: String? {
        guard let value = Bundle.main.object(forInfoDictionaryKey: "GitHubFeedbackToken") as? String else {
            return nil
        }
        let token = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !token.isEmpty, !token.hasPrefix("$(") else {
            return nil
        }
        return token
    }
}

private struct GitHubIssueCreateRequest: Encodable {
    var title: String
    var body: String
    var labels: [String]
}

private struct GitHubIssueCreateResponse: Decodable {
    var htmlURL: String

    private enum CodingKeys: String, CodingKey {
        case htmlURL = "html_url"
    }
}

private struct GitHubErrorResponse: Decodable {
    var message: String
}

private enum AppFeedbackError: LocalizedError {
    case notConfigured
    case invalidResponse
    case github(String)

    var errorDescription: String? {
        switch self {
        case .notConfigured:
            "GitHub feedback is not configured for this build."
        case .invalidResponse:
            "GitHub returned an invalid response."
        case .github(let message):
            "GitHub issue creation failed: \(message)"
        }
    }
}
