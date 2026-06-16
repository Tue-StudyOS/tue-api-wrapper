import Foundation

struct StudyAssistantConfiguration: Sendable {
    var almaBaseURLString: String
    var portalAPIBaseURLString: String
    var hasCredentials: Bool
}

enum StudyAssistantDataError: LocalizedError {
    case emptyQuery
    case invalidAlmaURL
    case missingCredentials
    case missingPortalBackend

    var errorDescription: String? {
        switch self {
        case .emptyQuery:
            "Enter a non-empty search query."
        case .invalidAlmaURL:
            "The Alma base URL in Settings is invalid."
        case .missingCredentials:
            "Connect your university account in Settings before using study snapshot or grades."
        case .missingPortalBackend:
            "The bundled portal backend URL is not available in this build."
        }
    }
}

struct StudyAssistantDataSource: Sendable {
    let configuration: StudyAssistantConfiguration

    private let keychain = KeychainCredentialsStore()

    func loadStudySnapshot(limit: Int) async throws -> String {
        let credentials = try loadCredentials()
        let almaBaseURL = try loadAlmaBaseURL()
        let cappedLimit = capped(limit, max: 8)

        async let lectureSnapshot = AlmaClient(baseURL: almaBaseURL).fetchUpcomingLectures(
            credentials: credentials,
            limit: cappedLimit
        )
        async let taskSnapshot = UniversityPortalClient(credentialsLoader: keychain).fetchTasksAndDeadlines(
            taskLimit: cappedLimit,
            deadlineLimit: cappedLimit
        )

        let (lectures, tasks) = try await (lectureSnapshot, taskSnapshot)

        var lines = [
            "Study snapshot",
            "Source term: \(lectures.sourceTerm)",
            ""
        ]

        if let personName = lectures.personName?.trimmingCharacters(in: .whitespacesAndNewlines),
           !personName.isEmpty {
            lines.append("Profile: \(personName)")
        }

        if let semesterCredits = lectures.semesterCredits {
            lines.append("Saved semester credits: \(semesterCredits.displayText)")
        }

        lines.append("")
        lines.append("Upcoming lectures:")
        if lectures.events.isEmpty {
            lines.append("- No upcoming Alma lectures were returned.")
        } else {
            for event in lectures.events.prefix(cappedLimit) {
                lines.append("- \(event.title) | \(event.timeRangeText)\(studyAssistantFormattedLocation(event.location))")
            }
        }

        lines.append("")
        lines.append("ILIAS tasks:")
        if tasks.tasks.isEmpty {
            lines.append("- No open ILIAS tasks were returned.")
        } else {
            for task in tasks.tasks.prefix(cappedLimit) {
                lines.append("- \(task.title)\(studyAssistantFormattedTaskRange(start: task.start, end: task.end))")
            }
        }

        lines.append("")
        lines.append("ILIAS submissions:")
        if tasks.iliasAssignments.isEmpty {
            lines.append("- No visible ILIAS submissions were returned.")
        } else {
            for deadline in tasks.iliasAssignments.prefix(cappedLimit) {
                let due = deadline.assignment.dueAt ?? deadline.assignment.dueHint ?? "No deadline exposed"
                lines.append("- \(deadline.assignment.title) | \(deadline.courseTitle) | \(due)")
            }
        }

        lines.append("")
        lines.append("Moodle deadlines:")
        if tasks.deadlines.isEmpty {
            lines.append("- No actionable Moodle deadlines were returned.")
        } else {
            for deadline in tasks.deadlines.prefix(cappedLimit) {
                lines.append("- \(deadline.title)\(studyAssistantFormattedDeadlineCourse(deadline.courseName))\(studyAssistantFormattedDeadlineTime(deadline))")
            }
        }

        return lines.joined(separator: "\n")
    }

    func loadGrades(limit: Int) async throws -> String {
        let almaBaseURL = try loadAlmaBaseURL()
        let cappedLimit = capped(limit, max: 10)
        let payload = try await UniversityGradesClient(
            credentialsLoader: keychain,
            almaBaseURL: almaBaseURL
        ).fetchGrades(
            examLimit: cappedLimit,
            moodleLimit: cappedLimit
        )

        let passedCount = payload.exams.filter(studyAssistantIsPassed).count
        let gradedCount = payload.exams.filter(studyAssistantIsExplicitlyGraded).count
        let trackedCredits = payload.exams
            .compactMap { exam in
                exam.cp?
                    .replacingOccurrences(of: ",", with: ".")
                    .trimmingCharacters(in: .whitespacesAndNewlines)
            }
            .compactMap(Double.init)
            .reduce(0, +)

        var lines = [
            "Current grades",
            "Passed Alma records: \(passedCount)",
            "Explicitly graded Alma records: \(gradedCount)",
            "Tracked credits from visible Alma rows: \(studyAssistantFormattedCredits(trackedCredits))",
            ""
        ]

        lines.append("Alma exam records:")
        if payload.exams.isEmpty {
            lines.append("- No Alma exam rows were returned.")
        } else {
            for exam in payload.exams.prefix(cappedLimit) {
                lines.append("- \(exam.title)\(studyAssistantFormattedExamMeta(exam))")
            }
        }

        lines.append("")
        lines.append("Moodle grades:")
        if payload.moodleGrades.items.isEmpty {
            lines.append("- No Moodle grades were returned.")
        } else {
            for grade in payload.moodleGrades.items.prefix(cappedLimit) {
                lines.append("- \(grade.courseTitle)\(studyAssistantFormattedMoodleGrade(grade))")
            }
        }

        return lines.joined(separator: "\n")
    }

    func searchCourses(query: String, limit: Int) async throws -> String {
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedQuery.isEmpty else {
            throw StudyAssistantDataError.emptyQuery
        }
        guard let client = BackendClient(baseURLString: configuration.portalAPIBaseURLString) else {
            throw StudyAssistantDataError.missingPortalBackend
        }

        var request = ModuleSearchRequest()
        request.query = trimmedQuery
        request.maxResults = capped(limit, max: 12)
        let response = try await client.searchModules(request)

        var lines = [
            "Course search results for \"\(trimmedQuery)\"",
            "Returned results: \(response.returnedResults)\(studyAssistantFormattedTotalResults(response.totalResults))",
            ""
        ]

        if response.results.isEmpty {
            lines.append("No public Alma modules matched the query.")
        } else {
            for result in response.results.prefix(request.maxResults) {
                lines.append("- \(result.title)\(studyAssistantFormattedCourseMeta(result))")
            }
        }

        return lines.joined(separator: "\n")
    }

    func searchTalks(query: String, limit: Int) async throws -> String {
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedQuery.isEmpty else {
            throw StudyAssistantDataError.emptyQuery
        }

        let searchPool = try await TalksClient().fetchTalks(scope: .upcoming, limit: 100)
        let matches = searchPool.filter { talk in
            [
                talk.title,
                talk.description ?? "",
                talk.location ?? "",
                talk.speakerName ?? "",
                talk.speakerBio ?? "",
                talk.tags.map(\.name).joined(separator: " ")
            ]
            .joined(separator: "\n")
            .localizedCaseInsensitiveContains(trimmedQuery)
        }

        let cappedLimit = capped(limit, max: 10)
        var lines = [
            "Upcoming talks matching \"\(trimmedQuery)\"",
            "Matches: \(matches.count)",
            ""
        ]

        if matches.isEmpty {
            lines.append("No upcoming public talks matched the query.")
        } else {
            for talk in matches.prefix(cappedLimit) {
                lines.append("- \(talk.title)\(studyAssistantFormattedTalkMeta(talk))")
            }
        }

        return lines.joined(separator: "\n")
    }

    private func loadCredentials() throws -> AlmaCredentials {
        guard let credentials = try keychain.load() else {
            throw StudyAssistantDataError.missingCredentials
        }
        return credentials
    }

    private func loadAlmaBaseURL() throws -> URL {
        guard let url = URL(string: configuration.almaBaseURLString),
              ["http", "https"].contains(url.scheme?.lowercased() ?? "") else {
            throw StudyAssistantDataError.invalidAlmaURL
        }
        return url
    }

    private func capped(_ value: Int, max: Int) -> Int {
        Swift.max(1, Swift.min(value, max))
    }
}
