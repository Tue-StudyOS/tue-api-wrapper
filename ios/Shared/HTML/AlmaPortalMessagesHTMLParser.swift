import Foundation

enum AlmaPortalMessagesHTMLParser {
    static func extractListContract(from html: String, pageURL: URL) throws -> AlmaPortalMessagesListContract {
        guard let form = firstForm(id: "startPage", in: html),
              let opening = HTMLRegex.firstCapture("(<form\\b[^>]*>)", in: form) else {
            throw AlmaClientError.timetableMissing("Could not find the Alma start-page form.")
        }
        let action = HTMLRegex.attribute("action", in: opening) ?? ""
        guard let actionURL = URL(string: action, relativeTo: pageURL)?.absoluteURL else {
            throw AlmaClientError.invalidURL
        }
        let formID = HTMLRegex.attribute("id", in: opening) ?? "startPage"
        let trigger = findMessagesToggle(in: form)
        let renderIDs = [sectionID(from: trigger), messagesInfoboxID(in: form)].compactMap(\.self)
        return AlmaPortalMessagesListContract(
            pageURL: pageURL,
            actionURL: actionURL,
            formID: formID,
            payload: formPayload(in: form),
            toggleTriggerName: trigger,
            partialRenderIDs: renderIDs
        )
    }

    static func buildExpandRequest(_ contract: AlmaPortalMessagesListContract) -> URLRequest? {
        guard let trigger = contract.toggleTriggerName, !contract.partialRenderIDs.isEmpty else {
            return nil
        }
        var payload = contract.payload
        payload[contract.formID] = contract.formID
        payload["activePageElementId"] = trigger
        payload["javax.faces.behavior.event"] = "action"
        payload["javax.faces.partial.event"] = "click"
        payload["javax.faces.source"] = trigger
        payload["javax.faces.partial.ajax"] = "true"
        payload["javax.faces.partial.execute"] = contract.formID
        payload["javax.faces.partial.render"] = contract.partialRenderIDs.joined(separator: " ")

        var request = URLRequest(url: contract.actionURL)
        request.httpMethod = "POST"
        request.httpBody = HTTPFormEncoder.encode(payload)
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        return request
    }

    static func parsePage(_ html: String, pageURL: URL) -> AlmaPortalMessagesPage {
        AlmaPortalMessagesPage(pageURL: pageURL, items: parseItems(in: html, pageURL: pageURL))
    }

    static func parsePartialResponse(_ xml: String, pageURL: URL) throws -> AlmaPortalMessagesPage {
        guard xml.localizedCaseInsensitiveContains("<partial-response") else {
            return parsePage(xml, pageURL: pageURL)
        }
        for content in cdataUpdates(in: xml) where content.contains("portalMessagesContent") {
            return parsePage(content, pageURL: pageURL)
        }
        for content in cdataUpdates(in: xml) where content.contains("Meine Meldungen") {
            return parsePage(content, pageURL: pageURL)
        }
        throw AlmaClientError.timetableMissing("The Alma portal-messages response did not contain the messages list.")
    }

    private static func parseItems(in html: String, pageURL: URL) -> [AlmaPortalMessage] {
        HTMLRegex.matches("<li\\b[^>]*>.*?</li>", in: html).compactMap { match in
            guard let range = Range(match.range, in: html) else { return nil }
            let row = String(html[range])
            guard row.contains("portalMessageText") else { return nil }
            let titleHTML = HTMLRegex.firstCapture(
                "<[^>]+class=(['\"])[^'\"]*portalMessageText[^'\"]*\\1[^>]*>(.*?)</[^>]+>",
                in: row,
                group: 2
            ) ?? row
            let title = HTMLText.stripTags(titleHTML)
            guard !title.isEmpty else { return nil }

            let linkTag = HTMLRegex.firstCapture("(<a\\b[^>]*>)", in: row)
            let href = linkTag.flatMap { HTMLRegex.attribute("href", in: $0) }
            let target = linkTag.flatMap { HTMLRegex.attribute("target", in: $0)?.trimmedOrNil }
            let imageTag = HTMLRegex.firstCapture("(<img\\b[^>]*>)", in: row)
            let iconURL = imageTag
                .flatMap { HTMLRegex.attribute("src", in: $0) }
                .flatMap { absoluteString($0, pageURL: pageURL) }
            let messageID = HTMLRegex.firstCapture("'messageId'\\s*:\\s*'([^']+)'", in: row)
                ?? linkTag.flatMap { HTMLRegex.attribute("id", in: $0) }
                ?? title

            return AlmaPortalMessage(
                id: messageID,
                title: title,
                url: href.flatMap { absoluteString($0, pageURL: pageURL) },
                target: target,
                iconURL: iconURL,
                createdAtLabel: menuDate(in: row)
            )
        }
    }

    private static func firstForm(id: String, in html: String) -> String? {
        HTMLRegex.matches("<form\\b[^>]*>.*?</form>", in: html).compactMap { match in
            guard let range = Range(match.range, in: html) else { return nil }
            let form = String(html[range])
            guard let opening = HTMLRegex.firstCapture("(<form\\b[^>]*>)", in: form),
                  HTMLRegex.attribute("id", in: opening) == id else {
                return nil
            }
            return form
        }.first
    }

    private static func findMessagesToggle(in form: String) -> String? {
        for match in HTMLRegex.matches("<(?:a|button)\\b[^>]*>", in: form) {
            guard let range = Range(match.range, in: form) else { continue }
            let tag = String(form[range])
            let name = HTMLRegex.attribute("id", in: tag) ?? HTMLRegex.attribute("name", in: tag) ?? ""
            let title = HTMLRegex.attribute("title", in: tag) ?? HTMLRegex.attribute("aria-label", in: tag) ?? ""
            if name.contains(":titlemin_portletInstanceId_") && title.contains("Meine Meldungen") {
                return name
            }
            if name.contains(":min_portletInstanceId_") && title.contains("Meine Meldungen") {
                return name
            }
        }
        return nil
    }

    private static func sectionID(from trigger: String?) -> String? {
        guard let trigger else { return nil }
        let prefix = trigger.components(separatedBy: ":titlemin_").first?
            .components(separatedBy: ":min_").first
        guard let prefix, let suffix = trigger.components(separatedBy: "_").last else {
            return nil
        }
        return "\(prefix):portletInstanceId_\(suffix)"
    }

    private static func messagesInfoboxID(in form: String) -> String? {
        HTMLRegex.matches("<[^>]+id=(['\"])(.*?)\\1[^>]*>", in: form).compactMap { match in
            guard let range = Range(match.range(at: 2), in: form) else { return nil }
            let value = String(form[range])
            return value.hasSuffix(":messages-infobox") ? value : nil
        }.first
    }

    private static func formPayload(in form: String) -> [String: String] {
        var payload: [String: String] = [:]
        for match in HTMLRegex.matches("<input\\b[^>]*>", in: form) {
            guard let range = Range(match.range, in: form) else { continue }
            let tag = String(form[range])
            guard let name = HTMLRegex.attribute("name", in: tag), !name.isEmpty else { continue }
            let type = HTMLRegex.attribute("type", in: tag)?.lowercased()
            guard !["button", "file", "image", "password", "reset", "submit"].contains(type ?? "") else { continue }
            payload[name] = HTMLRegex.attribute("value", in: tag) ?? ""
        }
        return payload
    }

    private static func cdataUpdates(in xml: String) -> [String] {
        HTMLRegex.matches("<update\\b[^>]*><!\\[CDATA\\[(.*?)\\]\\]></update>", in: xml).compactMap {
            guard let range = Range($0.range(at: 1), in: xml) else { return nil }
            return String(xml[range])
        }
    }

    private static func menuDate(in row: String) -> String? {
        guard let value = HTMLRegex.firstCapture(
            "<small\\b[^>]*class=(['\"])[^'\"]*menuListDate[^'\"]*\\1[^>]*>(.*?)</small>",
            in: row,
            group: 2
        ) else {
            return nil
        }
        return HTMLText.stripTags(value).trimmedOrNil
    }

    private static func absoluteString(_ value: String, pageURL: URL) -> String? {
        URL(string: value, relativeTo: pageURL)?.absoluteURL.absoluteString
    }
}
