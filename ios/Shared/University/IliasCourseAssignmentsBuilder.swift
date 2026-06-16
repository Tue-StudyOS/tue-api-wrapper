import Foundation

enum IliasCourseAssignmentsBuilder {
    static func exerciseItems(in course: IliasContentPage) -> [IliasContentItem] {
        course.sections
            .flatMap(\.items)
            .filter(isExerciseItem)
    }

    static func isExerciseItem(_ item: IliasContentItem) -> Bool {
        if let kind = item.kind?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased(),
           exerciseKinds.contains(kind) {
            return true
        }
        guard let url = URL(string: item.url),
              let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else {
            return false
        }
        let path = components.path.lowercased()
        if path.contains("/goto.php/exc/") || path.hasSuffix("/goto.php/exc") {
            return true
        }
        var query: [String: String] = [:]
        for item in components.queryItems ?? [] {
            query[item.name.lowercased()] = (item.value ?? "").lowercased()
        }
        return query["baseclass"] == "ilexercisehandlergui" || query["cmdclass"] == "ilobjexercisegui"
    }

    private static let exerciseKinds: Set<String> = ["übung", "exercise", "exercises"]
}
