import Foundation

struct UniversityPortalClient {
    private let credentialsLoader: UniversityCredentialsLoading
    private let iliasClientFactory: (AlmaCredentials) -> UniversityIliasTaskLoading
    private let moodleClientFactory: (AlmaCredentials) -> UniversityMoodleDeadlineLoading

    init(
        credentialsLoader: UniversityCredentialsLoading,
        iliasClientFactory: @escaping (AlmaCredentials) -> UniversityIliasTaskLoading = { IliasOnDeviceClient(credentials: $0) },
        moodleClientFactory: @escaping (AlmaCredentials) -> UniversityMoodleDeadlineLoading = { MoodleOnDeviceClient(credentials: $0) }
    ) {
        self.credentialsLoader = credentialsLoader
        self.iliasClientFactory = iliasClientFactory
        self.moodleClientFactory = moodleClientFactory
    }

    func fetchTasksAndDeadlines(
        taskLimit: Int = 20,
        iliasCourseLimit: Int = 20,
        iliasAssignmentLimit: Int = 50,
        deadlineDays: Int = 14,
        deadlineLimit: Int = 30
    ) async throws -> UniversityTaskSnapshot {
        guard let credentials = try credentialsLoader.load() else {
            throw UniversityPortalError.missingCredentials
        }

        async let tasksFetch = portalResult("ILIAS tasks") {
            try await iliasClientFactory(credentials).fetchTasks(limit: taskLimit)
        }
        async let iliasAssignmentsFetch = portalResult("ILIAS submissions") {
            try await iliasClientFactory(credentials).fetchAssignmentDeadlines(
                courseLimit: iliasCourseLimit,
                assignmentLimit: iliasAssignmentLimit
            )
        }
        async let deadlinesFetch = portalResult("Moodle deadlines") {
            try await moodleClientFactory(credentials).fetchDeadlines(days: deadlineDays, limit: deadlineLimit)
        }
        let (taskResult, iliasAssignmentResult, deadlineResult) = await (
            tasksFetch,
            iliasAssignmentsFetch,
            deadlinesFetch
        )
        return UniversityTaskSnapshot(
            tasks: taskResult.value ?? [],
            iliasAssignments: iliasAssignmentResult.value ?? [],
            deadlines: deadlineResult.value ?? [],
            refreshedAt: Date(),
            warnings: [taskResult.warning, iliasAssignmentResult.warning, deadlineResult.warning].compactMap(\.self)
        )
    }

    private func portalResult<Value>(
        _ label: String,
        operation: () async throws -> Value
    ) async -> PortalResult<Value> {
        do {
            return .success(try await operation())
        } catch {
            return .failure(portalWarning(label: label, error: error))
        }
    }

    private func portalWarning(label: String, error: Error) -> String {
        let message = error.localizedDescription
        if message.localizedCaseInsensitiveContains("SAML handoff") {
            return "\(label) could not finish the university login handoff."
        }
        return "\(label) could not be loaded: \(message)"
    }
}

private enum PortalResult<Value> {
    case success(Value)
    case failure(String)

    var value: Value? {
        guard case .success(let value) = self else { return nil }
        return value
    }

    var warning: String? {
        guard case .failure(let message) = self else { return nil }
        return message
    }
}
