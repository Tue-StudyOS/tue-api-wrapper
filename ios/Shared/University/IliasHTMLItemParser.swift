import Foundation

enum IliasHTMLItemParser {
    static func blocks(in html: String, containingClasses classes: [String]) -> [String] {
        let lookaheads = classes
            .map { "(?=[^'\"]*\\b\(NSRegularExpression.escapedPattern(for: $0))\\b)" }
            .joined()
        let pattern = "<[^>]*class\\s*=\\s*(['\"])\(lookaheads)[^'\"]*\\1[^>]*>"
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

    static func firstActionElement(in block: String) -> (title: String, url: String)? {
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

    static func itemProperties(in block: String) -> [String: String] {
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

    static func resolve(_ rawURL: String, pageURL: URL) -> URL? {
        URL(string: rawURL, relativeTo: pageURL)?.absoluteURL
    }

    static func isLoginOrHandoffPage(_ html: String) -> Bool {
        unauthenticatedMarkers.contains(where: html.contains)
    }

    private static let unauthenticatedMarkers = [
        "SAML" + "Response",
        "j_username",
        "j_" + "password",
        "shib_login.php",
        "Login mit zentraler Universitäts-Kennung"
    ]
}
