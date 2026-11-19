import Foundation

enum UniversityDirectoryHTMLParser {
    static func searchForm(in html: String, pageURL: URL) throws -> UniversityDirectorySearchForm {
        try checkAvailability(at: pageURL)
        let formTag = try firstFormTag(in: html)
        let actionURL = try resolve(HTMLRegex.attribute("action", in: formTag) ?? "", pageURL: pageURL)
        let queryFieldName = try inputName(matching: "NameTextBox", type: "text", in: html)
        guard let button = submitButton(matching: "SearchButton", in: html) else {
            throw UniversityPortalError.parsing("The public directory search button is missing.")
        }
        return UniversityDirectorySearchForm(
            form: UniversityHTMLForm(actionURL: actionURL, payload: inputPayload(in: html, includeSubmit: false)),
            queryFieldName: queryFieldName,
            searchButtonName: button.name,
            searchButtonValue: button.value
        )
    }

    static func searchResponse(from html: String, query: String, pageURL: URL) throws -> UniversityDirectorySearchResponse {
        try checkAvailability(at: pageURL)
        let title = firstHeading(in: primaryContent(in: html)) ?? "People"
        let pageName = pageURL.lastPathComponent.lowercased()
        return switch pageName {
        case "searchresultpersons.aspx":
            UniversityDirectorySearchResponse(
                query: query,
                title: title,
                outcome: .people(try peoplePage(from: html, title: title, pageURL: pageURL))
            )
        case "singleperson.aspx":
            UniversityDirectorySearchResponse(
                query: query,
                title: title,
                outcome: .person(person(from: html, title: title))
            )
        case "searchresultorganizations.aspx":
            UniversityDirectorySearchResponse(
                query: query,
                title: title,
                outcome: .organizations(try organizationsPage(from: html, title: title, pageURL: pageURL))
            )
        case "singleorganization.aspx":
            UniversityDirectorySearchResponse(
                query: query,
                title: title,
                outcome: .organization(try organization(from: html, title: title, pageURL: pageURL))
            )
        case "emptyresult.aspx":
            UniversityDirectorySearchResponse(query: query, title: title, outcome: .empty(message: pageMessage(in: html)))
        case "sizelimitexceeded.aspx":
            UniversityDirectorySearchResponse(
                query: query,
                title: title,
                outcome: .tooManyResults(message: pageMessage(in: html))
            )
        default:
            throw UniversityPortalError.parsing("The public university directory returned an unsupported result page.")
        }
    }

    private static func checkAvailability(at pageURL: URL) throws {
        if pageURL.lastPathComponent.caseInsensitiveCompare("Maintenance.aspx") == .orderedSame {
            throw UniversityPortalError.portal("The university directory is temporarily unavailable for maintenance. Try again later.")
        }
    }

    private static func peoplePage(from html: String, title: String, pageURL: URL) throws -> UniversityDirectoryPeoplePage {
        let primary = primaryContent(in: html)
        var sections = parseSectionedPersonResults(in: primary)
        if sections.isEmpty {
            let items = parsePersonItems(in: primary)
            if !items.isEmpty {
                sections = [UniversityDirectoryPersonSection(title: title, items: items)]
            }
        }
        guard !sections.isEmpty else {
            throw UniversityPortalError.parsing("The directory returned a people-results page without visible entries.")
        }
        return UniversityDirectoryPeoplePage(
            title: title,
            form: try pageForm(in: html, pageURL: pageURL),
            sections: sections
        )
    }

    private static func organizationsPage(
        from html: String,
        title: String,
        pageURL: URL
    ) throws -> UniversityDirectoryOrganizationResultsPage {
        let primary = primaryContent(in: html)
        let items: [UniversityDirectoryOrganizationSummary] = HTMLRegex.matches(
            #"<a\b[^>]*href\s*=\s*(['"])(.*?)\1[^>]*>(.*?)</a>"#,
            in: primary
        ).compactMap { match in
            guard let href = rangeString(match.range(at: 2), in: primary),
                  let action = eventAction(from: href),
                  let label = rangeString(match.range(at: 3), in: primary)?.normalizedDirectoryText.trimmedOrNil else {
                return nil
            }
            return UniversityDirectoryOrganizationSummary(name: label, action: action)
        }
        guard !items.isEmpty else {
            throw UniversityPortalError.parsing("The directory returned an organization-results page without visible entries.")
        }
        return UniversityDirectoryOrganizationResultsPage(
            title: title,
            form: try pageForm(in: html, pageURL: pageURL),
            items: items
        )
    }

    private static func person(from html: String, title: String) -> UniversityDirectoryPerson {
        let primary = primaryContent(in: html)
        let tables = HTMLRegex.matches(#"<table\b[^>]*>(.*?)</table>"#, in: primary).compactMap {
            rangeString($0.range(at: 1), in: primary)
        }
        let attributes = tables.first.map { parseFields(in: $0) } ?? []
        let sections: [UniversityDirectoryContactSection] = HTMLRegex.matches(
            #"<div\b[^>]*class\s*=\s*(['"])[^'"]*\bcp_title\b[^'"]*\1[^>]*>.*?<span[^>]*>(.*?)</span>.*?</div>\s*<div\b[^>]*class\s*=\s*(['"])[^'"]*\bcp_content\b[^'"]*\3[^>]*>.*?<table\b[^>]*>(.*?)</table>"#,
            in: primary
        ).compactMap { match in
            guard let rawTitle = rangeString(match.range(at: 2), in: primary)?.normalizedDirectoryText.trimmedOrNil,
                  let table = rangeString(match.range(at: 4), in: primary) else {
                return nil
            }
            let fields = parseFields(in: table)
            guard !fields.isEmpty else {
                return nil
            }
            return UniversityDirectoryContactSection(title: rawTitle, fields: fields)
        }
        return UniversityDirectoryPerson(
            name: title,
            summary: firstSubheading(in: primary),
            attributes: attributes,
            contactSections: sections
        )
    }

    private static func organization(from html: String, title: String, pageURL: URL) throws -> UniversityDirectoryOrganization {
        let primary = primaryContent(in: html)
        let fields = HTMLRegex.firstCapture(#"<table\b[^>]*>(.*?)</table>"#, in: primary)
            .map { parseFields(in: $0) }
            ?? []
        let personListAction = submitButton(matching: "PersonListButton", in: primary)
            .map { UniversityDirectoryPageAction.submit(name: $0.0, value: $0.1) }
        return UniversityDirectoryOrganization(
            name: title,
            form: try pageForm(in: html, pageURL: pageURL),
            fields: fields,
            personListAction: personListAction
        )
    }

    private static func parseSectionedPersonResults(in html: String) -> [UniversityDirectoryPersonSection] {
        HTMLRegex.matches(#"<h2\b[^>]*>(.*?)</h2>\s*<ul\b[^>]*>(.*?)</ul>"#, in: html).compactMap { match in
            guard let rawTitle = rangeString(match.range(at: 1), in: html)?.normalizedDirectoryText.trimmedOrNil,
                  let listBody = rangeString(match.range(at: 2), in: html) else {
                return nil
            }
            let items = parsePersonItems(in: listBody)
            guard !items.isEmpty else {
                return nil
            }
            return UniversityDirectoryPersonSection(title: rawTitle, items: items)
        }
    }

    private static func parsePersonItems(in html: String) -> [UniversityDirectoryPersonSummary] {
        HTMLRegex.matches(#"<li\b[^>]*>\s*<a\b[^>]*href\s*=\s*(['"])(.*?)\1[^>]*>(.*?)</a>\s*(?:<span\b[^>]*>\s*\((.*?)\)\s*</span>)?"#, in: html).compactMap { match in
            guard let href = rangeString(match.range(at: 2), in: html),
                  let action = eventAction(from: href),
                  let name = rangeString(match.range(at: 3), in: html)?.normalizedDirectoryText.trimmedOrNil else {
                return nil
            }
            let subtitle = rangeString(match.range(at: 4), in: html)?.normalizedDirectoryText.trimmedOrNil
            return UniversityDirectoryPersonSummary(name: name, subtitle: subtitle, action: action)
        }
    }

    private static func parseFields(in tableHTML: String) -> [UniversityDirectoryField] {
        HTMLRegex.matches(#"<tr\b[^>]*>\s*<t[dh]\b[^>]*>(.*?)</t[dh]>\s*<t[dh]\b[^>]*>(.*?)</t[dh]>"#, in: tableHTML).compactMap { match in
            guard let label = rangeString(match.range(at: 1), in: tableHTML)?.normalizedDirectoryText.trimmedOrNil,
                  let value = rangeString(match.range(at: 2), in: tableHTML)?.normalizedDirectoryText.trimmedOrNil else {
                return nil
            }
            return UniversityDirectoryField(label: label, value: value)
        }
    }

    private static func pageForm(in html: String, pageURL: URL) throws -> UniversityHTMLForm {
        let formTag = try firstFormTag(in: html)
        return UniversityHTMLForm(
            actionURL: try resolve(HTMLRegex.attribute("action", in: formTag) ?? "", pageURL: pageURL),
            payload: inputPayload(in: html, includeSubmit: false)
        )
    }

    private static func pageMessage(in html: String) -> String {
        let primary = primaryContent(in: html)
        let paragraphs = HTMLRegex.matches(#"<p\b[^>]*>(.*?)</p>"#, in: primary).compactMap { match in
            rangeString(match.range(at: 1), in: primary)?.normalizedDirectoryText.trimmedOrNil
        }
        return paragraphs.joined(separator: "\n\n")
    }

    private static func firstFormTag(in html: String) throws -> String {
        guard let formTag = HTMLRegex.firstCapture(#"(<form\b[^>]*>)"#, in: html) else {
            throw UniversityPortalError.parsing("The public directory did not return a searchable form.")
        }
        return formTag
    }

    private static func inputName(matching marker: String, type: String, in html: String) throws -> String {
        guard let name = inputTags(in: html).first(where: {
            HTMLRegex.attribute("type", in: $0)?.caseInsensitiveCompare(type) == .orderedSame
                && (HTMLRegex.attribute("name", in: $0)?.contains(marker) == true)
        }).flatMap({ HTMLRegex.attribute("name", in: $0) }) else {
            throw UniversityPortalError.parsing("The public directory search field is missing.")
        }
        return name
    }

    private static func submitButton(matching marker: String, in html: String) -> (name: String, value: String)? {
        inputTags(in: html).compactMap { tag in
            guard HTMLRegex.attribute("type", in: tag)?.caseInsensitiveCompare("submit") == .orderedSame,
                  let name = HTMLRegex.attribute("name", in: tag),
                  name.contains(marker) else {
                return nil
            }
            return (name, HTMLRegex.attribute("value", in: tag) ?? "")
        }.first
    }

    private static func inputPayload(in html: String, includeSubmit: Bool) -> [(String, String)] {
        inputTags(in: html).compactMap { tag in
            guard let name = HTMLRegex.attribute("name", in: tag), !name.isEmpty else {
                return nil
            }
            let type = HTMLRegex.attribute("type", in: tag)?.lowercased() ?? ""
            if ["checkbox", "radio", "button", "image", "file", "reset"].contains(type) {
                return nil
            }
            if type == "submit" && !includeSubmit {
                return nil
            }
            return (name, HTMLRegex.attribute("value", in: tag) ?? "")
        }
    }

    private static func inputTags(in html: String) -> [String] {
        HTMLRegex.matches(#"<input\b[^>]*>"#, in: html).compactMap {
            rangeString($0.range(at: 0), in: html)
        }
    }

    private static func primaryContent(in html: String) -> String {
        guard let start = html.range(of: #"<div id="content">"#, options: [.regularExpression, .caseInsensitive]) else {
            return html
        }
        let suffix = String(html[start.upperBound...])
        let markers = [
            suffix.range(of: #"<div id="nextSearch">"#, options: [.regularExpression, .caseInsensitive])?.lowerBound,
            suffix.range(of: #"<h1>\s*Suche\s*</h1>"#, options: [.regularExpression, .caseInsensitive])?.lowerBound,
        ].compactMap(\.self)
        guard let end = markers.min(by: { $0 < $1 }) else {
            return suffix
        }
        return String(suffix[..<end])
    }

    private static func firstHeading(in html: String) -> String? {
        HTMLRegex.firstCapture(#"<h1\b[^>]*>(.*?)</h1>"#, in: html)?.normalizedDirectoryText.trimmedOrNil
    }

    private static func firstSubheading(in html: String) -> String? {
        HTMLRegex.firstCapture(#"<h3\b[^>]*>(.*?)</h3>"#, in: html)?.normalizedDirectoryText.trimmedOrNil
    }

    private static func eventAction(from href: String) -> UniversityDirectoryPageAction? {
        let decoded = HTMLText.decodeEntities(href)
        guard let target = HTMLRegex.firstCapture(#"__doPostBack\(['"]([^'"]+)['"]"#, in: decoded)?.trimmedOrNil else {
            return nil
        }
        return .eventTarget(target)
    }

    private static func rangeString(_ range: NSRange, in text: String) -> String? {
        guard range.location != NSNotFound, let swiftRange = Range(range, in: text) else {
            return nil
        }
        return String(text[swiftRange])
    }

    private static func resolve(_ rawURL: String, pageURL: URL) throws -> URL {
        guard let url = URL(string: rawURL, relativeTo: pageURL)?.absoluteURL else {
            throw UniversityPortalError.invalidURL("The public directory returned an invalid URL.")
        }
        return url
    }
}
