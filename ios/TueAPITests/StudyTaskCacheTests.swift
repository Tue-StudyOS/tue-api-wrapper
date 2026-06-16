import XCTest
@testable import TueAPI

final class StudyTaskCacheTests: XCTestCase {
    func testSaveAndLoadRoundTripsVisibleSnapshot() throws {
        let (cache, suiteName) = try makeCache()
        defer { UserDefaults().removePersistentDomain(forName: suiteName) }

        let snapshot = UniversityTaskSnapshot(
            tasks: [
                IliasTask(
                    title: "Read notes",
                    url: "https://ovidius.uni-tuebingen.de/goto.php/task/1",
                    itemType: "Task",
                    start: nil,
                    end: "Tomorrow"
                )
            ],
            iliasAssignments: [
                IliasAssignmentDeadline(
                    courseTitle: "NLP",
                    courseURL: "https://ovidius.uni-tuebingen.de/goto.php/crs/1",
                    exerciseTitle: "Submissions",
                    exerciseURL: "https://ovidius.uni-tuebingen.de/goto.php/exc/1",
                    assignment: IliasExerciseAssignment(
                        title: "Practice exam",
                        url: "https://ovidius.uni-tuebingen.de/ilias.php?ass_id=1",
                        dueHint: nil,
                        dueAt: "19. Jun 2026, 00:00",
                        requirement: nil,
                        lastSubmission: nil,
                        submissionType: "File",
                        status: "Open",
                        teamActionURL: nil
                    )
                )
            ],
            deadlines: [
                MoodleDeadline(
                    rawId: 7,
                    title: "Quiz",
                    dueAt: nil,
                    formattedTime: "Today, 18:00",
                    courseName: "Moodle course",
                    courseId: 42,
                    actionURL: "https://moodle.zdv.uni-tuebingen.de/mod/quiz/view.php?id=7",
                    isActionable: true
                )
            ],
            refreshedAt: Date(timeIntervalSince1970: 1_780_000_000),
            warnings: ["Moodle warning"]
        )

        try cache.save(snapshot)

        let restored = try XCTUnwrap(cache.load())
        XCTAssertEqual(restored.tasks.first?.title, "Read notes")
        XCTAssertEqual(restored.iliasAssignments.first?.assignment.title, "Practice exam")
        XCTAssertEqual(restored.deadlines.first?.title, "Quiz")
        XCTAssertEqual(restored.warningMessage, "Moodle warning")
        XCTAssertEqual(restored.refreshedAt, snapshot.refreshedAt)
    }

    private func makeCache() throws -> (StudyTaskCache, String) {
        let suiteName = "StudyTaskCacheTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        return (StudyTaskCache(defaults: defaults), suiteName)
    }
}
