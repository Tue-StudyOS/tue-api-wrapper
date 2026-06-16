import Foundation

enum AppConfig {
    static let almaBaseURLDefaultsKey = "almaBaseURL"
    static let ambientRefreshMaxAge: TimeInterval = 2 * 60 * 60
    static let backgroundRefreshInterval: TimeInterval = 2 * 60 * 60
    static let submissionRemindersEnabledKey = "submissionRemindersEnabled"
    static let submissionReminderWindow: TimeInterval = 3 * 24 * 60 * 60
    static let portalAPIBaseURLString = PortalAPIConfig.baseURLString
}
