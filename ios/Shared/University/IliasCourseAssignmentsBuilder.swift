import Foundation

enum IliasCourseAssignmentsBuilder {
    static func exerciseItems(in course: IliasContentPage) -> [IliasContentItem] {
        course.sections
            .flatMap(\.items)
            .filter(isExerciseItem)
    }

    static func courseMemberships(in memberships: [IliasMembershipItem]) -> [IliasMembershipItem] {
        memberships.filter(isCourseMembership)
    }

    static func deadlines(
        course: IliasMembershipItem,
        groups: [IliasCourseExerciseAssignments]
    ) -> [IliasAssignmentDeadline] {
        groups.flatMap { group in
            group.assignments.map { assignment in
                IliasAssignmentDeadline(
                    courseTitle: course.title,
                    courseURL: course.url,
                    exerciseTitle: group.exercise.label,
                    exerciseURL: group.exercise.url,
                    assignment: assignment
                )
            }
        }
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

    private static func isCourseMembership(_ item: IliasMembershipItem) -> Bool {
        if let kind = item.kind?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased(),
           courseKinds.contains(kind) {
            return true
        }
        guard let url = URL(string: item.url) else {
            return false
        }
        let path = url.path.lowercased()
        return path.contains("/goto.php/crs/") || path.hasSuffix("/goto.php/crs")
    }

    private static let exerciseKinds: Set<String> = ["übung", "exercise", "exercises"]
    private static let courseKinds: Set<String> = ["kurs", "course"]
}
