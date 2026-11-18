import Foundation
import UserNotifications

enum LectureReminderSchedulerError: LocalizedError {
    case notificationsDisabled

    var errorDescription: String? {
        switch self {
        case .notificationsDisabled:
            "Notification permission is disabled. Enable notifications for TUE API in Settings to receive lecture reminders."
        }
    }
}

struct LectureReminderScheduleSummary: Equatable {
    var scheduledCount: Int
    var skippedCount: Int
}

enum LectureReminderScheduler {
    private static let identifierPrefix = "lectureReminder:"
    private static let maxPendingReminders = 64

    static func authorizationStatus() async -> UNAuthorizationStatus {
        await UNUserNotificationCenter.current().notificationSettings().authorizationStatus
    }

    static func requestAuthorization() async throws -> Bool {
        try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])
    }

    static func scheduleReminders(
        for events: [LectureEvent],
        leadTimeMinutes: Int,
        now: Date = Date()
    ) async throws -> LectureReminderScheduleSummary {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()

        guard canSchedule(status: settings.authorizationStatus) else {
            throw LectureReminderSchedulerError.notificationsDisabled
        }

        let leadTime = TimeInterval(leadTimeMinutes * 60)
        let upcomingRequests = events
            .sorted { $0.startDate < $1.startDate }
            .compactMap { request(for: $0, leadTime: leadTime, now: now) }

        let requests = Array(upcomingRequests.prefix(maxPendingReminders))
        let wantedIDs = Set(requests.map(\.identifier))

        // Diff against existing reminders: only cancel what's no longer needed,
        // only add what isn't already scheduled. Avoids a full cancel+rebuild on
        // every refresh when only a handful of events changed.
        let existingIDs = Set(await reminderIdentifiers(in: center))
        let toRemove = Array(existingIDs.subtracting(wantedIDs))
        if !toRemove.isEmpty {
            center.removePendingNotificationRequests(withIdentifiers: toRemove)
        }

        let toAdd = requests.filter { !existingIDs.contains($0.identifier) }
        for request in toAdd {
            try await center.add(request)
        }

        return LectureReminderScheduleSummary(
            scheduledCount: requests.count,
            skippedCount: max(upcomingRequests.count - requests.count, 0)
        )
    }

    @discardableResult
    static func cancelScheduledReminders() async -> Int {
        let center = UNUserNotificationCenter.current()
        let identifiers = await reminderIdentifiers(in: center)
        center.removePendingNotificationRequests(withIdentifiers: identifiers)
        return identifiers.count
    }

    static func pendingReminderCount() async -> Int {
        await reminderIdentifiers(in: UNUserNotificationCenter.current()).count
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

    private static func request(
        for event: LectureEvent,
        leadTime: TimeInterval,
        now: Date
    ) -> UNNotificationRequest? {
        let triggerDate = event.startDate.addingTimeInterval(-leadTime)
        guard !event.isCancelled, triggerDate > now else {
            return nil
        }

        let content = UNMutableNotificationContent()
        content.title = "Lecture starts soon"
        content.body = bodyText(for: event)
        content.sound = .default
        content.userInfo = ["lectureID": event.id]

        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Europe/Berlin") ?? .current
        let components = calendar.dateComponents(
            [.year, .month, .day, .hour, .minute],
            from: triggerDate
        )
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)

        return UNNotificationRequest(
            identifier: identifier(for: event),
            content: content,
            trigger: trigger
        )
    }

    private static func bodyText(for event: LectureEvent) -> String {
        let startTime = event.startDate.formatted(date: .omitted, time: .shortened)
        guard let location = event.location, !location.isEmpty else {
            return "\(event.title) starts at \(startTime)."
        }
        return "\(event.title) starts at \(startTime) in \(location)."
    }

    private static func identifier(for event: LectureEvent) -> String {
        "\(identifierPrefix)\(event.id)"
    }

    private static func reminderIdentifiers(in center: UNUserNotificationCenter) async -> [String] {
        let requests = await center.pendingNotificationRequests()
        return requests
            .map(\.identifier)
            .filter { $0.hasPrefix(identifierPrefix) }
    }
}
