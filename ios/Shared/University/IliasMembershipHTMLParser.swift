import Foundation

enum IliasMembershipHTMLParser {
    static func parse(_ html: String, pageURL: URL) throws -> [IliasMembershipItem] {
        let memberships = IliasHTMLItemParser
            .blocks(in: html, containingClasses: ["il-item", "il-std-item"])
            .compactMap { membership(in: $0, pageURL: pageURL) }

        if memberships.isEmpty, IliasHTMLItemParser.isLoginOrHandoffPage(html) {
            throw UniversityPortalError.parsing("The response did not look like an authenticated ILIAS membership overview.")
        }
        return memberships
    }

    private static func membership(in block: String, pageURL: URL) -> IliasMembershipItem? {
        guard let action = IliasHTMLItemParser.firstActionElement(in: block),
              let url = IliasHTMLItemParser.resolve(action.url, pageURL: pageURL) else {
            return nil
        }
        let properties = propertyLines(in: block)
        return IliasMembershipItem(
            title: action.title,
            url: url.absoluteString,
            kind: imageAlt(in: block),
            description: description(in: block),
            infoURL: infoURL(in: block, pageURL: pageURL)?.absoluteString,
            properties: properties
        )
    }

    private static func propertyLines(in block: String) -> [String] {
        IliasHTMLItemParser.itemProperties(in: block)
            .sorted { $0.key.localizedCaseInsensitiveCompare($1.key) == .orderedAscending }
            .map { "\($0.key): \($0.value)" }
    }

    private static func imageAlt(in block: String) -> String? {
        let pattern = #"<img\b[^>]*\balt\s*=\s*(['"])(.*?)\1[^>]*>"#
        guard let match = HTMLRegex.matches(pattern, in: block).first,
              let range = Range(match.range(at: 2), in: block) else {
            return nil
        }
        return HTMLText.decodeEntities(String(block[range])).nilIfBlank
    }

    private static func description(in block: String) -> String? {
        let pattern = #"<[^>]*class\s*=\s*(['"])[^'"]*\bil-item-description\b[^'"]*\1[^>]*>(.*?)</[^>]+>"#
        guard let match = HTMLRegex.matches(pattern, in: block).first,
              let range = Range(match.range(at: 2), in: block) else {
            return nil
        }
        return HTMLText.stripTags(String(block[range])).nilIfBlank
    }

    private static func infoURL(in block: String, pageURL: URL) -> URL? {
        let pattern = #"<button\b[^>]*\bdata-action\s*=\s*(['"])([^'"]*infoScreen[^'"]*)\1[^>]*>"#
        guard let match = HTMLRegex.matches(pattern, in: block).first,
              let range = Range(match.range(at: 2), in: block) else {
            return nil
        }
        return IliasHTMLItemParser.resolve(HTMLText.decodeEntities(String(block[range])), pageURL: pageURL)
    }
}

private extension String {
    var nilIfBlank: String? {
        let value = trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? nil : value
    }
}
