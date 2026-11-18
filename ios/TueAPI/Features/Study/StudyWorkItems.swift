import SwiftUI

extension AppModel {
    var studyWorkItems: [TodayUrgencyItem] {
        let moodleItems = deadlines.map {
            TodayUrgencyItem(
                id: "moodle-\($0.id)",
                dueDate: $0.dueAt.flatMap { SubmissionReminderDateParser.date(from: $0) },
                title: $0.title,
                subtitle: HTMLText.decodeEntities($0.courseName ?? "Moodle deadline"),
                detail: deadlineDetailText(for: $0),
                source: "Moodle",
                sourceURL: sourceURL($0.actionURL),
                systemImage: "calendar.badge.clock",
                tint: .orange
            )
        }
        let assignments = iliasAssignments.map {
            TodayUrgencyItem(
                id: "assignment-\($0.id)",
                dueDate: $0.assignment.dueAt.flatMap { SubmissionReminderDateParser.date(from: $0) },
                title: $0.assignment.title,
                subtitle: $0.courseTitle,
                detail: iliasAssignmentDetailText(for: $0),
                source: "ILIAS",
                sourceURL: sourceURL($0.assignment.url),
                status: $0.assignment.status,
                lastSubmission: $0.assignment.lastSubmission,
                requirement: $0.assignment.requirement,
                systemImage: "tray.and.arrow.up",
                tint: .accentColor
            )
        }
        let iliasTasks = tasks.map {
            TodayUrgencyItem(
                id: "ilias-\($0.id)",
                dueDate: $0.end.flatMap { SubmissionReminderDateParser.date(from: $0) },
                title: $0.title,
                subtitle: $0.itemType ?? "ILIAS task",
                detail: $0.end ?? "No deadline exposed",
                source: "ILIAS",
                sourceURL: sourceURL($0.url),
                systemImage: "checklist",
                tint: .accentColor
            )
        }
        let items = moodleItems + assignments + iliasTasks
        let dated = items.filter { $0.dueDate != nil }.sorted {
            ($0.dueDate ?? .distantFuture) < ($1.dueDate ?? .distantFuture)
        }
        return dated + items.filter { $0.dueDate == nil }
    }

    private func sourceURL(_ value: String?) -> URL? {
        guard let value, let url = URL(string: value), url.scheme == "https", url.host != nil else { return nil }
        return url
    }

    private func deadlineDetailText(for deadline: MoodleDeadline) -> String {
        if let formattedTime = deadline.formattedTime {
            let cleaned = HTMLText.stripTags(formattedTime)
            if !cleaned.isEmpty {
                return cleaned
            }
        }

        if let dueAt = deadline.dueAt {
            let cleaned = HTMLText.stripTags(dueAt)
            if !cleaned.isEmpty {
                return cleaned
            }
        }

        return "Due date unavailable"
    }

    private func iliasAssignmentDetailText(for deadline: IliasAssignmentDeadline) -> String {
        if let dueAt = deadline.assignment.dueAt?.trimmingCharacters(in: .whitespacesAndNewlines),
           !dueAt.isEmpty {
            return dueAt
        }
        if let dueHint = deadline.assignment.dueHint?.trimmingCharacters(in: .whitespacesAndNewlines),
           !dueHint.isEmpty {
            return dueHint
        }
        return deadline.exerciseTitle
    }
}
