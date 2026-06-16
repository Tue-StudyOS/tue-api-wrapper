import CryptoKit
import Foundation
import UserNotifications

enum SubmissionReminderSchedulerError: LocalizedError {
    case notificationsDisabled

    var errorDescription: String? {
        switch self {
        case .notificationsDisabled:
            "Notification permission is disabled. Enable notifications for TUE API in Settings to receive submission reminders."
        }
    }
}

struct SubmissionReminderCandidate: Equatable {
    var identifier: String
    var reminderKey: String
    var title: String
    var courseTitle: String
    var dueDate: Date
    var dueText: String
    var url: String
}

struct SubmissionReminderScheduleSummary: Equatable {
    var scheduledCount: Int
    var alreadyRemindedCount: Int
    var skippedCount: Int
}

enum SubmissionReminderScheduler {
    private static let identifierPrefix = "submissionReminder:"
    private static let reminderHistoryKey = "submissionReminderHistory"
    private static let maxPendingReminders = 32

    static func requestAuthorization() async throws -> Bool {
        try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])
    }

    static func scheduleReminders(
        for deadlines: [IliasAssignmentDeadline],
        now: Date = Date(),
        defaults: UserDefaults = .standard
    ) async throws -> SubmissionReminderScheduleSummary {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        guard canSchedule(status: settings.authorizationStatus) else {
            throw SubmissionReminderSchedulerError.notificationsDisabled
        }

        let candidates = deadlines
            .compactMap { candidate(for: $0, now: now) }
            .sorted { $0.dueDate < $1.dueDate }

        let history = reminderHistory(defaults: defaults)
        let freshCandidates = candidates.filter { !history.contains($0.reminderKey) }
        let limitedCandidates = Array(freshCandidates.prefix(maxPendingReminders))
        let eligibleIDs = Set(candidates.map(\.identifier))

        let existingIDs = Set(await reminderIdentifiers(in: center))
        let toRemove = Array(existingIDs.subtracting(eligibleIDs))
        if !toRemove.isEmpty {
            center.removePendingNotificationRequests(withIdentifiers: toRemove)
        }

        let toSchedule = limitedCandidates.filter { !existingIDs.contains($0.identifier) }
        for candidate in toSchedule {
            try await center.add(request(for: candidate))
        }

        if !toSchedule.isEmpty {
            saveReminderHistory(
                history.union(toSchedule.map(\.reminderKey)),
                activeCandidates: candidates,
                defaults: defaults
            )
        } else {
            saveReminderHistory(history, activeCandidates: candidates, defaults: defaults)
        }

        return SubmissionReminderScheduleSummary(
            scheduledCount: toSchedule.count,
            alreadyRemindedCount: candidates.count - freshCandidates.count,
            skippedCount: max(freshCandidates.count - limitedCandidates.count, 0)
        )
    }

    @discardableResult
    static func cancelScheduledReminders() async -> Int {
        let center = UNUserNotificationCenter.current()
        let identifiers = await reminderIdentifiers(in: center)
        center.removePendingNotificationRequests(withIdentifiers: identifiers)
        return identifiers.count
    }

    static func clearReminderHistory(defaults: UserDefaults = .standard) {
        defaults.removeObject(forKey: reminderHistoryKey)
    }

    static func candidate(
        for deadline: IliasAssignmentDeadline,
        now: Date = Date(),
        window: TimeInterval = AppConfig.submissionReminderWindow
    ) -> SubmissionReminderCandidate? {
        guard hasNoRecordedSubmission(deadline.assignment.lastSubmission),
              isStillOpen(status: deadline.assignment.status),
              let dueText = deadline.assignment.dueAt?.trimmedOrNil,
              let dueDate = SubmissionReminderDateParser.date(from: dueText) else {
            return nil
        }

        let remaining = dueDate.timeIntervalSince(now)
        guard remaining > 0, remaining <= window else {
            return nil
        }

        let key = "\(deadline.assignment.url)|\(dueText)"
        return SubmissionReminderCandidate(
            identifier: "\(identifierPrefix)\(digest(key))",
            reminderKey: key,
            title: deadline.assignment.title,
            courseTitle: deadline.courseTitle,
            dueDate: dueDate,
            dueText: dueText,
            url: deadline.assignment.url
        )
    }

    private static func request(for candidate: SubmissionReminderCandidate) -> UNNotificationRequest {
        let content = UNMutableNotificationContent()
        content.title = "Submission due soon"
        content.body = "\(candidate.title) in \(candidate.courseTitle) is due \(candidate.dueText). No submission is recorded."
        content.sound = .default
        content.userInfo = ["submissionURL": candidate.url]

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 60, repeats: false)
        return UNNotificationRequest(identifier: candidate.identifier, content: content, trigger: trigger)
    }

    private static func canSchedule(status: UNAuthorizationStatus) -> Bool {
        switch status {
        case .authorized, .provisional, .ephemeral:
            true
        case .denied, .notDetermined:
            false
        @unknown default:
            false
        }
    }

    private static func hasNoRecordedSubmission(_ value: String?) -> Bool {
        guard let text = normalized(value) else {
            return true
        }
        return [
            "keine abgabe",
            "no submission",
            "not submitted",
            "nothing submitted"
        ].contains { text.contains($0) }
    }

    private static func isStillOpen(status: String?) -> Bool {
        guard let text = normalized(status) else {
            return true
        }
        return ![
            "abgegeben",
            "submitted",
            "geschlossen",
            "closed",
            "beendet",
            "completed",
            "erledigt"
        ].contains { text.contains($0) }
    }

    private static func normalized(_ value: String?) -> String? {
        guard let value = value?.trimmedOrNil else {
            return nil
        }
        return value
            .folding(options: [.caseInsensitive, .diacriticInsensitive], locale: Locale(identifier: "de_DE"))
            .lowercased()
    }

    private static func reminderIdentifiers(in center: UNUserNotificationCenter) async -> [String] {
        let requests = await center.pendingNotificationRequests()
        return requests
            .map(\.identifier)
            .filter { $0.hasPrefix(identifierPrefix) }
    }

    private static func reminderHistory(defaults: UserDefaults) -> Set<String> {
        Set(defaults.stringArray(forKey: reminderHistoryKey) ?? [])
    }

    private static func saveReminderHistory(
        _ history: Set<String>,
        activeCandidates: [SubmissionReminderCandidate],
        defaults: UserDefaults
    ) {
        let activeKeys = Set(activeCandidates.map(\.reminderKey))
        defaults.set(Array(history.intersection(activeKeys)).sorted(), forKey: reminderHistoryKey)
    }

    private static func digest(_ value: String) -> String {
        let hash = SHA256.hash(data: Data(value.utf8))
        return hash.prefix(12).map { String(format: "%02x", $0) }.joined()
    }
}

private enum SubmissionReminderDateParser {
    private static let formats = [
        "d. MMM yyyy, HH:mm",
        "dd. MMM yyyy, HH:mm",
        "d. MMMM yyyy, HH:mm",
        "dd. MMMM yyyy, HH:mm",
        "d.M.yyyy, HH:mm",
        "dd.MM.yyyy, HH:mm"
    ]

    private static let locales = [
        Locale(identifier: "de_DE"),
        Locale(identifier: "en_US_POSIX")
    ]

    static func date(from value: String) -> Date? {
        let cleaned = value
            .replacingOccurrences(of: "\u{00a0}", with: " ")
            .replacingOccurrences(of: " Uhr", with: "")
            .trimmedOrNil
        guard let cleaned else {
            return nil
        }

        for locale in locales {
            for format in formats {
                let formatter = DateFormatter()
                formatter.calendar = Calendar(identifier: .gregorian)
                formatter.locale = locale
                formatter.timeZone = TimeZone(identifier: "Europe/Berlin")
                formatter.dateFormat = format
                if let date = formatter.date(from: cleaned) {
                    return date
                }
            }
        }
        return nil
    }
}
