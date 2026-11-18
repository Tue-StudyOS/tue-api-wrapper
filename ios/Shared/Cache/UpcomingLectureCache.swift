import Foundation

enum UpcomingLectureCacheError: LocalizedError {
    case sharedContainerUnavailable

    var errorDescription: String? {
        switch self {
        case .sharedContainerUnavailable:
            "The shared app group container is unavailable."
        }
    }
}

struct UpcomingLectureCache {
    private static let key = "upcomingLectureSnapshot"

    static func load() -> LectureSnapshot? {
        guard let defaults = UserDefaults(suiteName: AppGroup.identifier),
              let data = defaults.data(forKey: key) else {
            return nil
        }
        return try? JSONDecoder().decode(LectureSnapshot.self, from: data)
    }

    static func clear() {
        UserDefaults(suiteName: AppGroup.identifier)?.removeObject(forKey: key)
    }

    static func save(_ snapshot: LectureSnapshot) throws {
        guard let defaults = UserDefaults(suiteName: AppGroup.identifier) else {
            throw UpcomingLectureCacheError.sharedContainerUnavailable
        }
        let data = try JSONEncoder().encode(snapshot)
        defaults.set(data, forKey: key)
    }
}
