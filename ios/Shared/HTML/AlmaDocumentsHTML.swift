import Foundation

struct AlmaDocumentOption: Hashable, Identifiable {
    let id: String
    let title: String
}

struct AlmaDocumentForm {
    let action: URL
    let fields: [String: String]
    let reports: [AlmaDocumentOption]
    let documentsTab: AlmaDocumentOption?
    let start: AlmaDocumentOption?
    let poll: AlmaDocumentOption?
    let termField: String?
    let terms: [AlmaDocumentOption]

    static func parse(_ html: String, at url: URL) throws -> Self {
        let content = AlmaDocumentsHTML.markup(html)
        guard let form = AlmaDocumentsHTML.elements("form", in: content).first(where: {
            HTMLRegex.attribute("id", in: $0.tag) == "studyserviceForm"
        }), let action = HTMLRegex.attribute("action", in: form.tag),
            let actionURL = URL(string: action, relativeTo: url)?.absoluteURL else {
            throw AlmaDocumentError.unavailable("Alma’s study-service form was not available.")
        }

        let inputs = AlmaDocumentsHTML.tags("input", in: form.content)
        var fields: [String: String] = [:]
        for input in inputs {
            guard let name = HTMLRegex.attribute("name", in: input),
                  !["button", "checkbox", "file", "image", "password", "submit", "radio"]
                    .contains(HTMLRegex.attribute("type", in: input)?.lowercased() ?? "") else { continue }
            fields[name] = HTMLRegex.attribute("value", in: input) ?? ""
        }

        let buttons = AlmaDocumentsHTML.elements("button", in: form.content)
        let actions = buttons.compactMap { button -> AlmaDocumentOption? in
            guard let name = HTMLRegex.attribute("name", in: button.tag) else { return nil }
            let text = HTMLText.stripTags(button.content)
            return AlmaDocumentOption(id: name, title: text)
        }
        let controls = actions + inputs.compactMap { input in
            HTMLRegex.attribute("name", in: input).map {
                AlmaDocumentOption(id: $0, title: HTMLRegex.attribute("value", in: input) ?? "")
            }
        }

        let selects = AlmaDocumentsHTML.elements("select", in: form.content)
        let termSelect = selects.first {
            HTMLRegex.attribute("name", in: $0.tag)?.hasSuffix(":setting_0:setting_input") == true
        }
        let termField = termSelect.flatMap { HTMLRegex.attribute("name", in: $0.tag) }
        let terms = AlmaDocumentsHTML.elements("option", in: termSelect?.content ?? "").compactMap { option -> AlmaDocumentOption? in
            guard let value = HTMLRegex.attribute("value", in: option.tag), !value.isEmpty,
                  !AlmaDocumentsHTML.hasAttribute("disabled", in: option.tag) else { return nil }
            return AlmaDocumentOption(id: value, title: HTMLText.stripTags(option.content))
        }

        for select in selects {
            guard let name = HTMLRegex.attribute("name", in: select.tag) else { continue }
            let options = AlmaDocumentsHTML.elements("option", in: select.content)
            let option = options.first { AlmaDocumentsHTML.hasAttribute("selected", in: $0.tag) }
                ?? options.first
            if let option { fields[name] = HTMLRegex.attribute("value", in: option.tag) }
        }

        return Self(
            action: actionURL,
            fields: fields,
            reports: actions.filter { $0.id.hasSuffix(":job2") && !$0.title.isEmpty },
            documentsTab: actions.first { $0.id.hasPrefix("studyserviceForm:content.") && $0.title.localizedCaseInsensitiveContains("Bescheide") },
            start: controls.first { $0.id.hasSuffix(":startJob") },
            poll: controls.first { $0.id.hasSuffix(":jobDownloadPoll:poll") },
            termField: termField,
            terms: terms
        )
    }
}

enum AlmaDocumentsHTML {
    static func markup(_ html: String) -> String {
        guard html.contains("<partial-response") else { return html }
        return HTMLRegex.matches(#"<!\[CDATA\[(.*?)\]\]>"#, in: html).compactMap { match in
            Range(match.range(at: 1), in: html).map { String(html[$0]) }
        }.joined(separator: "\n")
    }

    static func downloadLinks(_ html: String, at url: URL) -> [URL] {
        tags("a", in: markup(html)).compactMap { tag in
            guard let href = HTMLRegex.attribute("href", in: tag),
                  let target = URL(string: href, relativeTo: url)?.absoluteURL,
                  URLComponents(url: target, resolvingAgainstBaseURL: true)?.queryItems?
                    .contains(where: { $0.name == "state" && $0.value == "docdownload" }) == true else { return nil }
            return target
        }
    }

    static func elements(_ name: String, in html: String) -> [(tag: String, content: String)] {
        HTMLRegex.matches("(<\(name)\\b[^>]*>)(.*?)</\(name)\\s*>", in: html).compactMap { match in
            guard let tag = Range(match.range(at: 1), in: html),
                  let content = Range(match.range(at: 2), in: html) else { return nil }
            return (String(html[tag]), String(html[content]))
        }
    }

    static func tags(_ name: String, in html: String) -> [String] {
        HTMLRegex.matches("<\(name)\\b[^>]*>", in: html).compactMap { match in
            Range(match.range, in: html).map { String(html[$0]) }
        }
    }

    static func hasAttribute(_ name: String, in tag: String) -> Bool {
        !HTMLRegex.matches("\\s\(name)(?=[\\s=>])", in: tag).isEmpty
    }
}

enum AlmaDocumentError: LocalizedError {
    case unavailable(String)

    var errorDescription: String? {
        switch self {
        case .unavailable(let message): message
        }
    }
}
