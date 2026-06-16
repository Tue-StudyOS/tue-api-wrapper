import XCTest
@testable import TueAPI

final class UniversityPortalClientTests: XCTestCase {
    func testFetchTasksAndDeadlinesRequiresSavedCredentials() async throws {
        let client = UniversityPortalClient(
            credentialsLoader: EmptyUniversityCredentialsLoader(),
            iliasClientFactory: { _ in UnusedIliasTaskLoader() },
            moodleClientFactory: { _ in UnusedMoodleDeadlineLoader() }
        )

        do {
            _ = try await client.fetchTasksAndDeadlines()
            XCTFail("Expected missing credentials to throw.")
        } catch let error as UniversityPortalError {
            XCTAssertEqual(error, .missingCredentials)
            XCTAssertEqual(error.localizedDescription, "Save university credentials before loading tasks and deadlines.")
        }
    }

    func testFetchTasksAndDeadlinesKeepsPartialDataWhenOnePortalHandoffFails() async throws {
        let client = UniversityPortalClient(
            credentialsLoader: SavedUniversityCredentialsLoader(),
            iliasClientFactory: { _ in SuccessfulIliasTaskLoader() },
            moodleClientFactory: { _ in FailingMoodleDeadlineLoader() }
        )

        let snapshot = try await client.fetchTasksAndDeadlines()

        XCTAssertEqual(snapshot.tasks.count, 1)
        XCTAssertEqual(snapshot.iliasAssignments.count, 1)
        XCTAssertEqual(snapshot.deadlines.count, 0)
        XCTAssertEqual(snapshot.warnings, ["Moodle deadlines could not finish the university login handoff."])
    }
}

private struct EmptyUniversityCredentialsLoader: UniversityCredentialsLoading {
    func load() throws -> AlmaCredentials? {
        nil
    }
}

private struct SavedUniversityCredentialsLoader: UniversityCredentialsLoading {
    func load() throws -> AlmaCredentials? {
        AlmaCredentials(username: "student", password: "secret")
    }
}

private struct UnusedIliasTaskLoader: UniversityIliasTaskLoading {
    func fetchTasks(limit _: Int) async throws -> [IliasTask] {
        XCTFail("ILIAS should not be called without credentials.")
        return []
    }

    func fetchAssignmentDeadlines(courseLimit _: Int, assignmentLimit _: Int) async throws -> [IliasAssignmentDeadline] {
        XCTFail("ILIAS should not be called without credentials.")
        return []
    }
}

private struct UnusedMoodleDeadlineLoader: UniversityMoodleDeadlineLoading {
    func fetchDeadlines(days _: Int, limit _: Int) async throws -> [MoodleDeadline] {
        XCTFail("Moodle should not be called without credentials.")
        return []
    }
}

private struct SuccessfulIliasTaskLoader: UniversityIliasTaskLoading {
    func fetchTasks(limit _: Int) async throws -> [IliasTask] {
        [
            IliasTask(
                title: "Assignment",
                url: "https://ovidius.uni-tuebingen.de/goto.php/exc_1",
                itemType: "Exercise",
                start: nil,
                end: "Tomorrow"
            )
        ]
    }

    func fetchAssignmentDeadlines(courseLimit _: Int, assignmentLimit _: Int) async throws -> [IliasAssignmentDeadline] {
        [
            IliasAssignmentDeadline(
                courseTitle: "Practical Machine Learning",
                courseURL: "https://ovidius.uni-tuebingen.de/goto.php/crs/1",
                exerciseTitle: "Assignments",
                exerciseURL: "https://ovidius.uni-tuebingen.de/goto.php/exc/1",
                assignment: IliasExerciseAssignment(
                    title: "Assignment 5",
                    url: "https://ovidius.uni-tuebingen.de/ilias.php?ass_id=5",
                    dueHint: nil,
                    dueAt: "19. Jun 2026, 00:00",
                    requirement: "Verpflichtend",
                    lastSubmission: "Bisher keine Abgabe",
                    submissionType: "Datei",
                    status: "Nicht bewertet",
                    teamActionURL: nil
                )
            )
        ]
    }
}

private struct FailingMoodleDeadlineLoader: UniversityMoodleDeadlineLoading {
    func fetchDeadlines(days _: Int, limit _: Int) async throws -> [MoodleDeadline] {
        throw UniversityPortalError.loginFailed("Could not complete the university SAML handoff.")
    }
}
