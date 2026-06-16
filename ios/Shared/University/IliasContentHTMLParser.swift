import Foundation

enum IliasContentHTMLParser {
    static func parse(_ html: String, pageURL: URL) throws -> IliasContentPage {
        let sections = IliasHTMLItemParser
            .blocks(in: html, containingClasses: ["ilContainerBlock"])
            .compactMap { section(in: $0, pageURL: pageURL) }

        if sections.isEmpty, IliasHTMLItemParser.isLoginOrHandoffPage(html) {
            throw UniversityPortalError.parsing("The response did not look like an authenticated ILIAS content page.")
        }
        return IliasContentPage(
            title: title(in: html) ?? "ILIAS",
            pageURL: pageURL.absoluteString,
            sections: sections
        )
    }

    private static func section(in block: String, pageURL: URL) -> IliasContentSection? {
        let items = IliasHTMLItemParser
            .blocks(in: block, containingClasses: ["ilContainerListItemOuter"])
            .compactMap { item(in: $0, pageURL: pageURL) }
        guard !items.isEmpty else {
            return nil
        }
        let label = HTMLRegex
            .firstCapture(#"<h2\b[^>]*>(.*?)</h2>"#, in: block)
            .map(HTMLText.stripTags) ?? ""
        guard !label.isEmpty else {
            return nil
        }
        return IliasContentSection(label: label, items: items)
    }

    private static func item(in block: String, pageURL: URL) -> IliasContentItem? {
        guard let action = IliasHTMLItemParser.firstActionElement(in: block),
              let url = IliasHTMLItemParser.resolve(action.url, pageURL: pageURL) else {
            return nil
        }
        return IliasContentItem(
            label: action.title,
            url: url.absoluteString,
            kind: iconAlt(in: block),
            properties: itemProperties(in: block)
        )
    }

    private static func title(in html: String) -> String? {
        HTMLRegex.firstCapture(#"<title[^>]*>(.*?)</title>"#, in: html)
            .map(HTMLText.stripTags)
    }

    private static func iconAlt(in block: String) -> String? {
        HTMLRegex
            .firstCapture(#"<img\b[^>]*\balt\s*=\s*(['"])(.*?)\1"#, in: block, group: 2)
            .map(HTMLText.decodeEntities)
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .flatMap { $0.isEmpty ? nil : $0 }
    }

    private static func itemProperties(in block: String) -> [String] {
        let pattern = #"<[^>]*class\s*=\s*(['"])[^'"]*\bil_ItemProperty\b[^'"]*\1[^>]*>(.*?)</[^>]+>"#
        return HTMLRegex.matches(pattern, in: block).compactMap { match in
            guard let range = Range(match.range(at: 2), in: block) else {
                return nil
            }
            let value = HTMLText.stripTags(String(block[range]))
            return value.isEmpty ? nil : value
        }
    }
}
