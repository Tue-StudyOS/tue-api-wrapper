import XCTest
@testable import TueAPI

final class SubmissionReminderSchedulerTests: XCTestCase {
    func testCandidateMatchesUnsubmittedAssignmentInsideThreeDayWindow() throws {
        let candidate = try XCTUnwrap(
            SubmissionReminderScheduler.candidate(
                for: assignment(
                    dueAt: "19. Jun 2026, 00:00",
                    lastSubmission: "Bisher keine Abgabe",
                    status: "Nicht bewertet"
                ),
                now: Self.date("2026-06-16 12:00")
            )
        )

        XCTAssertEqual(candidate.title, "Assignment 5")
        XCTAssertEqual(candidate.courseTitle, "Practical Machine Learning")
        XCTAssertEqual(candidate.dueText, "19. Jun 2026, 00:00")
    }

    func testCandidateIgnoresAssignmentOutsideThreeDayWindow() throws {
        let candidate = SubmissionReminderScheduler.candidate(
            for: assignment(
                dueAt: "23. Jun 2026, 00:00",
                lastSubmission: "Bisher keine Abgabe",
                status: "Nicht bewertet"
            ),
            now: try Self.date("2026-06-16 12:00")
        )

        XCTAssertNil(candidate)
    }

    func testCandidateIgnoresRecordedSubmission() throws {
        let candidate = SubmissionReminderScheduler.candidate(
            for: assignment(
                dueAt: "19. Jun 2026, 00:00",
                lastSubmission: "18. Jun 2026, 15:20",
                status: "Nicht bewertet"
            ),
            now: try Self.date("2026-06-16 12:00")
        )

        XCTAssertNil(candidate)
    }

    func testCandidateIgnoresClosedStatus() throws {
        let candidate = SubmissionReminderScheduler.candidate(
            for: assignment(
                dueAt: "19. Jun 2026, 00:00",
                lastSubmission: "Bisher keine Abgabe",
                status: "Geschlossen"
            ),
            now: try Self.date("2026-06-16 12:00")
        )

        XCTAssertNil(candidate)
    }

    private func assignment(
        dueAt: String,
        lastSubmission: String?,
        status: String?
    ) -> IliasAssignmentDeadline {
        IliasAssignmentDeadline(
            courseTitle: "Practical Machine Learning",
            courseURL: "https://ovidius.uni-tuebingen.de/goto.php/crs/1",
            exerciseTitle: "Assignments",
            exerciseURL: "https://ovidius.uni-tuebingen.de/goto.php/exc/1",
            assignment: IliasExerciseAssignment(
                title: "Assignment 5",
                url: "https://ovidius.uni-tuebingen.de/ilias.php?ass_id=5",
                dueHint: nil,
                dueAt: dueAt,
                requirement: "Verpflichtend",
                lastSubmission: lastSubmission,
                submissionType: "Datei",
                status: status,
                teamActionURL: nil
            )
        )
    }

    private static func date(_ value: String) throws -> Date {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Europe/Berlin")
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return try XCTUnwrap(formatter.date(from: value))
    }
}
