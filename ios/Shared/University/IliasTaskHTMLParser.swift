import Foundation

enum IliasTaskHTMLParser {
    static func parse(_ html: String, pageURL: URL) throws -> [IliasTask] {
        let blocks = itemBlocks(in: html)
        let tasks = blocks.compactMap { block -> IliasTask? in
            guard let titleLink = firstActionElement(in: block),
                  let url = resolve(titleLink.url, pageURL: pageURL) else {
                return nil
            }
            let properties = itemProperties(in: block)
            return IliasTask(
                title: titleLink.title,
                url: url.absoluteString,
                itemType: properties["Übung"] ?? properties["Kurs"] ?? properties["Typ"],
                start: properties["Beginn"],
                end: properties["Ende"]
            )
        }

        if tasks.isEmpty, unauthenticatedMarkers.contains(where: html.contains) {
            throw UniversityPortalError.parsing("The response did not look like an authenticated ILIAS task overview.")
        }
        return tasks
    }

    private static func itemBlocks(in html: String) -> [String] {
        let pattern = #"<[^>]*class\s*=\s*(['"])[^'"]*\bil-item\b[^'"]*\bil-std-item\b[^'"]*\1[^>]*>"#
        let matches = HTMLRegex.matches(pattern, in: html)
        guard !matches.isEmpty else {
            return []
        }

        return matches.enumerated().compactMap { index, match in
            guard let start = Range(match.range(at: 0), in: html)?.lowerBound else {
                return nil
            }
            let end: String.Index
            if index + 1 < matches.count,
               let next = Range(matches[index + 1].range(at: 0), in: html)?.lowerBound {
                end = next
            } else {
                end = html.endIndex
            }
            return String(html[start..<end])
        }
    }

    private static func firstActionElement(in block: String) -> (title: String, url: String)? {
        let pattern = #"<(a|button)\b[^>]*(href|data-action)\s*=\s*(['"])(.*?)\3[^>]*>(.*?)</\1>"#
        for match in HTMLRegex.matches(pattern, in: block) {
            guard let urlRange = Range(match.range(at: 4), in: block),
                  let titleRange = Range(match.range(at: 5), in: block) else {
                continue
            }
            let title = HTMLText.stripTags(String(block[titleRange]))
            guard !title.isEmpty else {
                continue
            }
            return (title, HTMLText.decodeEntities(String(block[urlRange])))
        }
        return nil
    }

    private static func itemProperties(in block: String) -> [String: String] {
        let pattern = #"<[^>]*class\s*=\s*(['"])[^'"]*\bil-item-property-name\b[^'"]*\1[^>]*>(.*?)</[^>]+>\s*<[^>]*class\s*=\s*(['"])[^'"]*\bil-item-property-value\b[^'"]*\3[^>]*>(.*?)</[^>]+>"#
        var properties: [String: String] = [:]
        for match in HTMLRegex.matches(pattern, in: block) {
            guard let nameRange = Range(match.range(at: 2), in: block),
                  let valueRange = Range(match.range(at: 4), in: block) else {
                continue
            }
            let name = HTMLText.stripTags(String(block[nameRange]))
            let value = HTMLText.stripTags(String(block[valueRange]))
            if !name.isEmpty {
                properties[name] = value
            }
        }
        return properties
    }

    private static func resolve(_ rawURL: String, pageURL: URL) -> URL? {
        URL(string: rawURL, relativeTo: pageURL)?.absoluteURL
    }

    private static let unauthenticatedMarkers = [
        "SAML" + "Response",
        "j_username",
        "j_" + "password",
        "shib_login.php",
        "Login mit zentraler Universitäts-Kennung"
    ]
}
