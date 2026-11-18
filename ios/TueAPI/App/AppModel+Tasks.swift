import Foundation

extension AppModel {
    func refreshTasks() async {
        guard tasksPhase != .loading else { return }
        tasksPhase = .loading
        let revision = credentialRevision

        do {
            let snapshot = try await UniversityPortalClient(credentialsLoader: keychain)
                .fetchTasksAndDeadlines()
            guard revision == credentialRevision else { return }
            let visibleSnapshot = StudyTaskCache.visibleSnapshot(from: snapshot)
            tasks = visibleSnapshot.tasks
            iliasAssignments = visibleSnapshot.iliasAssignments
            deadlines = visibleSnapshot.deadlines
            tasksWarning = visibleSnapshot.warningMessage
            tasksPhase = .loaded(snapshot.refreshedAt)
            try? StudyTaskCache.save(visibleSnapshot)
            await rescheduleSubmissionRemindersIfEnabled()
        } catch UniversityPortalError.missingCredentials {
            guard revision == credentialRevision else { return }
            tasks = []
            iliasAssignments = []
            deadlines = []
            tasksWarning = nil
            tasksPhase = .unavailable
            StudyTaskCache.clear()
            SubmissionReminderScheduler.clearReminderHistory()
            await SubmissionReminderScheduler.cancelScheduledReminders()
        } catch {
            guard revision == credentialRevision else { return }
            tasksWarning = nil
            tasksPhase = .failed(error.localizedDescription)
        }
    }

    func shouldRefreshTasks(maxAge: TimeInterval = AppConfig.ambientRefreshMaxAge) -> Bool {
        guard hasCredentials else {
            return false
        }

        switch tasksPhase {
        case .idle, .unavailable, .failed:
            return true
        case .loading:
            return false
        case .loaded(let refreshedAt):
            return Date().timeIntervalSince(refreshedAt) >= maxAge
        }
    }
}
