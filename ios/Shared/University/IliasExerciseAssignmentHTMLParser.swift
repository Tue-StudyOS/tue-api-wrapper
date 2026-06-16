import Foundation

enum IliasExerciseAssignmentHTMLParser {
    static func parse(_ html: String, pageURL: URL) throws -> [IliasExerciseAssignment] {
        let assignments = IliasHTMLItemParser
            .blocks(in: html, containingClasses: ["il-item", "il-std-item"])
            .compactMap { assignment(in: $0, pageURL: pageURL) }

        if assignments.isEmpty, IliasHTMLItemParser.isLoginOrHandoffPage(html) {
            throw UniversityPortalError.parsing("The response did not look like an authenticated ILIAS exercise page.")
        }
        return assignments
    }

    private static func assignment(in block: String, pageURL: URL) -> IliasExerciseAssignment? {
        guard let action = IliasHTMLItemParser.firstActionElement(in: block),
              let url = IliasHTMLItemParser.resolve(action.url, pageURL: pageURL) else {
            return nil
        }
        let properties = IliasHTMLItemParser.itemProperties(in: block)
        return IliasExerciseAssignment(
            title: action.title,
            url: url.absoluteString,
            dueHint: dueHint(in: block),
            dueAt: properties["Abgabetermin"],
            requirement: properties["Anforderung"],
            lastSubmission: properties["Datum der letzten Abgabe"],
            submissionType: properties["Type"],
            status: properties["Status"],
            teamActionURL: teamActionURL(in: block, pageURL: pageURL)?.absoluteString
        )
    }

    private static func dueHint(in block: String) -> String? {
        HTMLRegex
            .firstCapture(#"<[^>]*class\s*=\s*(['"])[^'"]*\bcol-sm-3\b[^'"]*\1[^>]*>(.*?)</[^>]+>"#, in: block, group: 2)
            .map(HTMLText.stripTags)
            .flatMap { $0.isEmpty ? nil : $0 }
    }

    private static func teamActionURL(in block: String, pageURL: URL) -> URL? {
        guard let raw = HTMLRegex.firstCapture(#"<button\b[^>]*\bdata-action\s*=\s*(['"])(.*?)\1"#, in: block, group: 2) else {
            return nil
        }
        return IliasHTMLItemParser.resolve(HTMLText.decodeEntities(raw), pageURL: pageURL)
    }
}
