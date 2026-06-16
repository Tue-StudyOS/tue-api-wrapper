import BackgroundTasks
import Foundation
import WidgetKit

enum StudyBackgroundRefreshService {
    static let taskIdentifier = "dev.sebastianboehler.tueapi.study-refresh"

    @discardableResult
    static func schedule(after interval: TimeInterval = AppConfig.backgroundRefreshInterval) -> Bool {
        let request = BGAppRefreshTaskRequest(identifier: taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: interval)

        do {
            try BGTaskScheduler.shared.submit(request)
            return true
        } catch {
            return false
        }
    }

    static func handleAppRefresh() async {
        schedule()
        _ = await refreshStudyData()
    }

    static func refreshStudyData() async -> Bool {
        async let lecturesRefreshed = refreshUpcomingLectures()
        async let tasksRefreshed = refreshTasks()
        let didRefreshLectures = await lecturesRefreshed
        let didRefreshTasks = await tasksRefreshed
        let refreshed = didRefreshLectures || didRefreshTasks
        if refreshed {
            WidgetCenter.shared.reloadAllTimelines()
        }
        return refreshed
    }

    private static func refreshUpcomingLectures() async -> Bool {
        do {
            let keychain = KeychainCredentialsStore()
            guard let credentials = try keychain.load(),
                  let baseURL = almaBaseURL() else {
                return false
            }

            let snapshot = try await AlmaClient(baseURL: baseURL)
                .fetchUpcomingLectures(credentials: credentials)
            try UpcomingLectureCache.save(snapshot)
            return true
        } catch {
            return false
        }
    }

    private static func refreshTasks() async -> Bool {
        do {
            let snapshot = try await UniversityPortalClient(credentialsLoader: KeychainCredentialsStore())
                .fetchTasksAndDeadlines()
            let visibleSnapshot = StudyTaskCache.visibleSnapshot(from: snapshot)
            try StudyTaskCache.save(visibleSnapshot)
            if UserDefaults.standard.bool(forKey: AppConfig.submissionRemindersEnabledKey) {
                _ = try? await SubmissionReminderScheduler.scheduleReminders(for: visibleSnapshot.iliasAssignments)
            }
            return true
        } catch UniversityPortalError.missingCredentials {
            StudyTaskCache.clear()
            SubmissionReminderScheduler.clearReminderHistory()
            await SubmissionReminderScheduler.cancelScheduledReminders()
            return false
        } catch {
            return false
        }
    }

    private static func almaBaseURL() -> URL? {
        let value = UserDefaults.standard.string(forKey: AppConfig.almaBaseURLDefaultsKey)
            ?? "https://alma.uni-tuebingen.de"
        guard let url = URL(string: value), url.scheme?.hasPrefix("http") == true else {
            return nil
        }
        return url
    }
}
