import Foundation

enum LectureWidgetPrivacy {
    static let detailsKey = "lectureWidgetShowsLockScreenDetails"

    static var showsDetails: Bool {
        UserDefaults(suiteName: AppGroup.identifier)?.bool(forKey: detailsKey) ?? false
    }
}
