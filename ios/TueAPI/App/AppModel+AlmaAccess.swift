import Foundation
import WidgetKit

extension AppModel {
    func almaAccessContext(for feature: String) throws -> (client: AlmaClient, credentials: AlmaCredentials) {
        guard let baseURL = URL(string: baseURLString),
              ["http", "https"].contains(baseURL.scheme?.lowercased() ?? "") else {
            throw AlmaClientError.invalidURL
        }
        guard let credentials = try keychain.load() else {
            throw AlmaClientError.courseRegistration("Connect your university account before trying to \(feature).")
        }
        return (AlmaClient(baseURL: baseURL), credentials)
    }

    func refreshUpcomingLectures() async {
        phase = .loading

        do {
            let (client, credentials) = try almaAccessContext(for: "refresh Alma")
            let snapshot = try await client.fetchUpcomingLectures(credentials: credentials)
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

    func shouldRefreshUpcomingLectures(maxAge: TimeInterval = AppConfig.ambientRefreshMaxAge) -> Bool {
        guard hasCredentials else {
            return false
        }
        guard let timetableRefreshedAt else {
            return true
        }
        return Date().timeIntervalSince(timetableRefreshedAt) >= maxAge
    }
}
