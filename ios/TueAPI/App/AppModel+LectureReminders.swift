import Foundation

extension AppModel {
    func refreshReminderStatus() async {
        guard remindersEnabled else {
            let pendingCount = await LectureReminderScheduler.pendingReminderCount()
            if pendingCount > 0 {
                await disableLectureReminders()
            }
            return
        }

        await rescheduleRemindersIfEnabled()
    }

    func enableLectureReminders() async {
        do {
            let granted = try await LectureReminderScheduler.requestAuthorization()
            guard granted else {
                remindersEnabled = false
                reminderMessage = LectureReminderSchedulerError.notificationsDisabled.localizedDescription
                return
            }

            remindersEnabled = true
            await rescheduleRemindersIfEnabled()
        } catch {
            remindersEnabled = false
            reminderMessage = error.localizedDescription
        }
    }

    func disableLectureReminders() async {
        remindersEnabled = false
        let removedCount = await LectureReminderScheduler.cancelScheduledReminders()
        reminderMessage = removedCount == 1 ? "Removed 1 scheduled lecture reminder." : "Removed \(removedCount) scheduled lecture reminders."
    }

    func setReminderLeadTime(minutes: Int) async {
        guard Self.reminderLeadTimeOptions.contains(minutes) else {
            reminderMessage = "Choose a supported reminder lead time."
            return
        }

        reminderLeadTimeMinutes = minutes
        if remindersEnabled {
            await rescheduleRemindersIfEnabled()
        } else {
            reminderMessage = "Reminders will use \(minutes) minutes once enabled."
        }
    }

    func rescheduleRemindersIfEnabled() async {
        guard remindersEnabled else {
            return
        }

        do {
            let summary = try await LectureReminderScheduler.scheduleReminders(
                for: events,
                leadTimeMinutes: reminderLeadTimeMinutes
            )
            reminderMessage = Self.reminderMessage(for: summary, leadTime: reminderLeadTimeMinutes)
        } catch LectureReminderSchedulerError.notificationsDisabled {
            remindersEnabled = false
            reminderMessage = LectureReminderSchedulerError.notificationsDisabled.localizedDescription
        } catch {
            reminderMessage = error.localizedDescription
        }
    }

    private static func reminderMessage(for summary: LectureReminderScheduleSummary, leadTime: Int) -> String {
        guard summary.scheduledCount > 0 else {
            return "No lecture reminders were scheduled. Refresh Alma after upcoming lectures are available, or choose a shorter reminder time."
        }

        let scheduled = summary.scheduledCount == 1 ? "1 lecture reminder" : "\(summary.scheduledCount) lecture reminders"
        let skipped = summary.skippedCount == 0 ? "" : " \(summary.skippedCount) later entries were skipped because iOS limits pending app notifications."
        return "Scheduled \(scheduled) \(leadTime) minutes before class.\(skipped)"
    }
}
