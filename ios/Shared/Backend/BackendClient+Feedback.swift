import Foundation

extension BackendClient {
    func fetchAppFeedbackStatus() async throws -> AppFeedbackStatusResponse {
        let url = try makeURL(path: "api/feedback/status", queryItems: [])
        let data = try await get(url)
        return try JSONDecoder().decode(AppFeedbackStatusResponse.self, from: data)
    }

    func submitAppFeedback(_ feedback: AppFeedbackIssueRequest) async throws -> AppFeedbackIssueResponse {
        let url = try makeURL(path: "api/feedback/issues", queryItems: [])
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = try JSONEncoder().encode(feedback)

        let data = try await execute(request)
        return try JSONDecoder().decode(AppFeedbackIssueResponse.self, from: data)
    }
}
