import Foundation
import Observation
import WidgetKit

@MainActor
@Observable
final class AppModel {
    static let reminderLeadTimeOptions = [5, 10, 15, 30, 60]

    var events: [LectureEvent]
    var semesterCredits: SemesterCreditSummary?
    var timetableRefreshedAt: Date?
    var profileName: String?
    var almaSourceTerm: String?
    var browseLectures: [AlmaCurrentLecture] = []
    var browseSelectedDate: String?
    var phase: LoadPhase = .idle
    var browsePhase: BrowsePhase = .idle
    var hasCredentials = false
    var liveActivityMessage: String?
    var remindersEnabled: Bool {
        didSet {
            UserDefaults.standard.set(remindersEnabled, forKey: Self.remindersEnabledKey)
        }
    }
    var reminderLeadTimeMinutes: Int {
        didSet {
            UserDefaults.standard.set(reminderLeadTimeMinutes, forKey: Self.reminderLeadTimeKey)
        }
    }
    var reminderMessage: String?
    var baseURLString: String {
        didSet {
            UserDefaults.standard.set(baseURLString, forKey: Self.baseURLKey)
        }
    }

    var portalAPIBaseURLString: String {
        AppConfig.portalAPIBaseURLString
    }

    var currentTermLabel: String? {
        almaSourceTerm
    }

    // Tasks and deadlines are fetched on-device with Keychain credentials.
    var tasks: [IliasTask] = []
    var iliasAssignments: [IliasAssignmentDeadline] = []
    var deadlines: [MoodleDeadline] = []
    var tasksPhase: TasksLoadPhase = .idle
    var tasksWarning: String?

    let keychain = KeychainCredentialsStore()
    private static let baseURLKey = "almaBaseURL"
    private static let remindersEnabledKey = "lectureRemindersEnabled"
    private static let reminderLeadTimeKey = "lectureReminderLeadTimeMinutes"

    // Shared date formatter for Alma date strings (allocated once)
    private static let almaDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "de_DE")
        f.dateFormat = "dd.MM.yyyy"
        return f
    }()

    init() {
        self.baseURLString = UserDefaults.standard.string(forKey: Self.baseURLKey) ?? "https://alma.uni-tuebingen.de"
        let cachedSnapshot = UpcomingLectureCache.load()
        self.events = Self.upcomingOnly(cachedSnapshot?.events ?? [])
        self.semesterCredits = cachedSnapshot?.semesterCredits
        self.timetableRefreshedAt = cachedSnapshot?.refreshedAt
        self.profileName = cachedSnapshot?.personName
        self.almaSourceTerm = cachedSnapshot?.sourceTerm
        self.hasCredentials = ((try? keychain.load()) ?? nil) != nil
        self.remindersEnabled = UserDefaults.standard.bool(forKey: Self.remindersEnabledKey)

        let savedLeadTime = UserDefaults.standard.integer(forKey: Self.reminderLeadTimeKey)
        if Self.reminderLeadTimeOptions.contains(savedLeadTime) {
            self.reminderLeadTimeMinutes = savedLeadTime
        } else {
            self.reminderLeadTimeMinutes = 15
        }
    }

    func saveCredentials(username: String, password: String) {
        let trimmedUsername = username.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedUsername.isEmpty, !password.isEmpty else {
            phase = .failed("Enter both username and password.")
            return
        }

        do {
            try keychain.save(AlmaCredentials(username: trimmedUsername, password: password))
            hasCredentials = true
            phase = .idle
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    func browseCurrentLectures(on date: Date) async {
        browsePhase = .loading

        do {
            guard let baseURL = URL(string: baseURLString), baseURL.scheme?.hasPrefix("http") == true else {
                throw AlmaClientError.invalidURL
            }

            let dateString = Self.almaDateString(from: date)
            let publicPage = try await AlmaClient(baseURL: baseURL).fetchCurrentLectures(date: dateString, limit: 200)

            guard let credentials = try keychain.load() else {
                browseLectures = publicPage.results
                browseSelectedDate = publicPage.selectedDate ?? dateString
                browsePhase = .loaded(browseSelectedDate, publicPage.results.count, .publicOnly)
                return
            }

            do {
                let authenticatedPage = try await AlmaClient(baseURL: baseURL).fetchCurrentLectures(
                    date: dateString,
                    limit: 200,
                    credentials: credentials
                )
                let merged = BrowseLectureMerger.merged(
                    publicPage.results,
                    authenticatedPage.results
                )
                browseLectures = merged
                browseSelectedDate = authenticatedPage.selectedDate ?? publicPage.selectedDate ?? dateString
                browsePhase = .loaded(
                    browseSelectedDate,
                    merged.count,
                    .publicAndAuthenticated(
                        authenticatedOnlyCount: BrowseLectureMerger.authenticatedOnlyCount(
                            publicPage.results,
                            authenticatedPage.results
                        )
                    )
                )
            } catch {
                browseLectures = publicPage.results
                browseSelectedDate = publicPage.selectedDate ?? dateString
                browsePhase = .loaded(
                    browseSelectedDate,
                    publicPage.results.count,
                    .publicOnlyAuthenticatedFailed(error.localizedDescription)
                )
            }
        } catch {
            browsePhase = .failed(error.localizedDescription)
        }
    }

    func deleteCredentials() {
        do {
            try keychain.delete()
            hasCredentials = false
            profileName = nil
            almaSourceTerm = nil
            phase = .idle
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    func refreshUpcomingLectures() async {
        phase = .loading

        do {
            guard let baseURL = URL(string: baseURLString), baseURL.scheme?.hasPrefix("http") == true else {
                throw AlmaClientError.invalidURL
            }
            guard let credentials = try keychain.load() else {
                throw AlmaClientError.loginFailed("Connect your university account before refreshing Alma.")
            }

            let snapshot = try await AlmaClient(baseURL: baseURL).fetchUpcomingLectures(credentials: credentials)
            try UpcomingLectureCache.save(snapshot)
            events = Self.upcomingOnly(snapshot.events)
            semesterCredits = snapshot.semesterCredits
            timetableRefreshedAt = snapshot.refreshedAt
            profileName = snapshot.personName
            almaSourceTerm = snapshot.sourceTerm
            phase = .loaded(snapshot.refreshedAt, snapshot.sourceTerm)
            WidgetCenter.shared.reloadAllTimelines()
            await rescheduleRemindersIfEnabled()
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    func startLiveActivity(for event: LectureEvent) {
        do {
            try LiveActivityController.start(for: event)
            liveActivityMessage = "Live Activity started for \(event.title)."
        } catch {
            liveActivityMessage = error.localizedDescription
        }
    }

    func endLiveActivities() async {
        await LiveActivityController.endAll()
        liveActivityMessage = "Live Activities ended."
    }

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

    private static func upcomingOnly(_ events: [LectureEvent]) -> [LectureEvent] {
        let now = Date()
        return events.filter { ($0.endDate ?? $0.startDate) >= now }
    }

    private func rescheduleRemindersIfEnabled() async {
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

    private static func almaDateString(from date: Date) -> String {
        almaDateFormatter.string(from: date)
    }
}

enum LoadPhase: Equatable {
    case idle
    case loading
    case loaded(Date, String)
    case failed(String)
}
