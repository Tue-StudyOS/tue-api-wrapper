import Foundation

extension AppModel {
    func refreshSubmissionReminderStatus() async {
        guard submissionRemindersEnabled else {
            await SubmissionReminderScheduler.cancelScheduledReminders()
            return
        }

        await rescheduleSubmissionRemindersIfEnabled()
    }

    func enableSubmissionReminders() async {
        do {
            let granted = try await SubmissionReminderScheduler.requestAuthorization()
            guard granted else {
                submissionRemindersEnabled = false
                submissionReminderMessage = SubmissionReminderSchedulerError.notificationsDisabled.localizedDescription
                return
            }

            submissionRemindersEnabled = true
            await rescheduleSubmissionRemindersIfEnabled()
        } catch {
            submissionRemindersEnabled = false
            submissionReminderMessage = error.localizedDescription
        }
    }

    func disableSubmissionReminders() async {
        submissionRemindersEnabled = false
        let removedCount = await SubmissionReminderScheduler.cancelScheduledReminders()
        SubmissionReminderScheduler.clearReminderHistory()
        submissionReminderMessage = removedCount == 1
            ? "Removed 1 scheduled submission reminder."
            : "Removed \(removedCount) scheduled submission reminders."
    }

    func rescheduleSubmissionRemindersIfEnabled() async {
        guard submissionRemindersEnabled else {
            return
        }

        do {
            let summary = try await SubmissionReminderScheduler.scheduleReminders(for: iliasAssignments)
            submissionReminderMessage = Self.submissionReminderMessage(for: summary)
        } catch SubmissionReminderSchedulerError.notificationsDisabled {
            submissionRemindersEnabled = false
            submissionReminderMessage = SubmissionReminderSchedulerError.notificationsDisabled.localizedDescription
        } catch {
            submissionReminderMessage = error.localizedDescription
        }
    }

    private static func submissionReminderMessage(for summary: SubmissionReminderScheduleSummary) -> String {
        if summary.scheduledCount > 0 {
            let scheduled = summary.scheduledCount == 1 ? "1 submission reminder" : "\(summary.scheduledCount) submission reminders"
            let skipped = summary.skippedCount == 0 ? "" : " \(summary.skippedCount) later submissions were skipped because iOS limits pending app notifications."
            return "Scheduled \(scheduled) for open ILIAS submissions due within three days.\(skipped)"
        }
        if summary.alreadyRemindedCount > 0 {
            return "Open ILIAS submissions due within three days were already reminded."
        }
        return "No open ILIAS submissions without a recorded upload are due within three days."
    }
}
