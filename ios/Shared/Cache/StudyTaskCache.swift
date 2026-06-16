import Foundation

enum StudyTaskCacheError: LocalizedError {
    case sharedContainerUnavailable

    var errorDescription: String? {
        switch self {
        case .sharedContainerUnavailable:
            "The shared app group container is unavailable."
        }
    }
}

struct StudyTaskCache {
    private static let defaultKey = "studyTaskSnapshot"

    private let defaults: UserDefaults
    private let key: String

    init(defaults: UserDefaults, key: String = Self.defaultKey) {
        self.defaults = defaults
        self.key = key
    }

    static func visibleSnapshot(from snapshot: UniversityTaskSnapshot) -> UniversityTaskSnapshot {
        UniversityTaskSnapshot(
            tasks: snapshot.tasks,
            iliasAssignments: snapshot.iliasAssignments,
            deadlines: snapshot.deadlines.filter { $0.isActionable },
            refreshedAt: snapshot.refreshedAt,
            warnings: snapshot.warnings
        )
    }

    static func load() -> UniversityTaskSnapshot? {
        guard let defaults = UserDefaults(suiteName: AppGroup.identifier) else {
            return nil
        }
        return StudyTaskCache(defaults: defaults).load()
    }

    static func save(_ snapshot: UniversityTaskSnapshot) throws {
        guard let defaults = UserDefaults(suiteName: AppGroup.identifier) else {
            throw StudyTaskCacheError.sharedContainerUnavailable
        }
        try StudyTaskCache(defaults: defaults).save(snapshot)
    }

    static func clear() {
        guard let defaults = UserDefaults(suiteName: AppGroup.identifier) else {
            return
        }
        StudyTaskCache(defaults: defaults).clear()
    }

    func load() -> UniversityTaskSnapshot? {
        guard let data = defaults.data(forKey: key) else {
            return nil
        }
        return try? JSONDecoder().decode(UniversityTaskSnapshot.self, from: data)
    }

    func save(_ snapshot: UniversityTaskSnapshot) throws {
        let data = try JSONEncoder().encode(snapshot)
        defaults.set(data, forKey: key)
    }

    func clear() {
        defaults.removeObject(forKey: key)
    }
}
