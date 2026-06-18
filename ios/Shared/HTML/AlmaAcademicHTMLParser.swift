import Foundation

enum AlmaAcademicHTMLParser {
    static func parseEnrollment(_ html: String) throws -> AlmaEnrollmentState {
        guard let form = block(named: "form", in: html, attribute: "id", value: "studentOverviewForm") else {
            throw AlmaClientError.timetableMissing("Could not find the Alma enrollment overview form.")
        }
        guard let select = block(
            named: "select",
            in: form,
            attribute: "name",
            value: "studentOverviewForm:enrollmentsDiv:termSelector:termPeriodDropDownList_input"
        ) else {
            throw AlmaClientError.timetableMissing("Could not find the Alma enrollment term selector.")
        }

        var terms: [String: String] = [:]
        var selectedTerm: String?
        for option in optionTags(in: select) {
            let label = HTMLText.stripTags(option)
            let value = HTMLRegex.attribute("value", in: option)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            guard !label.isEmpty, !value.isEmpty else {
                continue
            }
            terms[label] = value
            if option.localizedCaseInsensitiveContains("selected") {
                selectedTerm = label
            }
        }

        return AlmaEnrollmentState(
            selectedTerm: selectedTerm,
            availableTerms: terms,
            message: enrollmentMessage(in: form),
            personName: personName(in: html),
            entries: enrollmentRecords(in: form)
        )
    }

    static func parseExamOverview(_ html: String, limit: Int) throws -> [AlmaExamRecord] {
        let table = firstTable(containingClass: "treeTableWithIcons", in: html)
        let source = table ?? html
        let rows = examRows(in: source)
        guard table != nil || !rows.isEmpty else {
            throw AlmaClientError.timetableMissing("Could not find the Alma exam overview tree table.")
        }

        return Array(rows.prefix(max(1, limit)))
    }

    private static func examRows(in html: String) -> [AlmaExamRecord] {
        HTMLRegex.matches("<tr\\b[^>]*>.*?</tr>", in: html).compactMap { match -> AlmaExamRecord? in
            guard let range = Range(match.range, in: html) else {
                return nil
            }
            return parseExamRow(String(html[range]))
        }
    }

    private static func parseExamRow(_ row: String) -> AlmaExamRecord? {
        guard let level = examRowLevel(in: row),
            HTMLRegex.matches("<td\\b[^>]*>", in: row).count >= 10,
            let title = fieldText(in: row, suffixPattern: "(?:defaulttext|unDeftxt)") else {
            return nil
        }

        return AlmaExamRecord(
            level: level,
            kind: kindText(in: row),
            title: title,
            number: fieldText(in: row, suffixPattern: "elementnr"),
            attempt: fieldText(in: row, suffixPattern: "attempt"),
            grade: fieldText(in: row, suffixPattern: "grade"),
            cp: fieldText(in: row, suffixPattern: "bonus"),
            status: fieldText(in: row, suffixPattern: "workstatus")
        )
    }

    private static func examRowLevel(in row: String) -> Int? {
        let tag = openingTag(named: "tr", in: row) ?? ""
        return HTMLRegex.firstCapture("treeTableCellLevel(\\d+)", in: tag)
            .flatMap(Int.init)
            ?? HTMLRegex.firstCapture("treeTableCellLevel(\\d+)", in: row).flatMap(Int.init)
    }

    private static func enrollmentMessage(in form: String) -> String? {
        let text = HTMLText.stripTags(form)
        let pattern = "Sie haben bisher.+?(?:angemeldet\\.|zugelassen\\.)"
        return HTMLRegex.firstCapture("(\(pattern))", in: text)
    }

    private static func enrollmentRecords(in form: String) -> [AlmaEnrollmentRecord] {
        blocks(named: "h2", in: form).compactMap { heading -> AlmaEnrollmentRecord? in
            let headingText = HTMLText.stripTags(heading)
            guard let parsedHeading = parseEnrollmentHeading(headingText),
                  let headingRange = form.range(of: heading),
                  let table = nextBlock(named: "table", in: String(form[headingRange.upperBound...])) else {
                return nil
            }

            let cells = blocks(named: "td", in: table).map(HTMLText.stripTags)
            let scheduleText = scheduleText(from: cells)
            let statusText = cells.first { $0.contains("Ihr aktueller Status:") } ?? HTMLText.stripTags(table)
            let identity = enrollmentIdentity(
                category: parsedHeading.category,
                rawTitle: parsedHeading.rawTitle,
                scheduleText: scheduleText
            )

            return AlmaEnrollmentRecord(
                category: parsedHeading.category,
                title: identity.title,
                number: identity.number,
                eventType: identity.eventType,
                status: value(after: "Ihr aktueller Status", in: statusText),
                semester: value(after: "Semester der Leistung", in: statusText),
                scheduleText: scheduleText,
                detailURL: detailURL(in: table),
                attempt: value(after: "Versuch (gilt nur für Prüfungen)", in: statusText)
            )
        }
    }

    private static func parseEnrollmentHeading(_ text: String) -> (category: String, rawTitle: String)? {
        guard let category = HTMLRegex.firstCapture("^(Veranstaltung|Prüfung):\\s*", in: text),
              let rawTitle = HTMLRegex.firstCapture("^(?:Veranstaltung|Prüfung):\\s*(.+)$", in: text) else {
            return nil
        }
        return (category, rawTitle)
    }

    private static func enrollmentIdentity(
        category: String,
        rawTitle: String,
        scheduleText: String?
    ) -> (eventType: String?, number: String?, title: String) {
        if category == "Prüfung" {
            let split = splitCode(rawTitle)
            return (category, split.number, examTitle(from: scheduleText) ?? split.title)
        }

        if let match = HTMLRegex.matches("([A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*\\d+[A-Z]*|GTCNEURO)\\s+(.+)$", in: rawTitle).first,
           let codeRange = Range(match.range(at: 1), in: rawTitle),
           let titleRange = Range(match.range(at: 2), in: rawTitle) {
            let eventType = String(rawTitle[..<codeRange.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
            return (
                eventType.isEmpty ? category : eventType,
                String(rawTitle[codeRange]),
                String(rawTitle[titleRange]).trimmingCharacters(in: .whitespacesAndNewlines)
            )
        }

        let split = splitCode(rawTitle)
        return (category, split.number, split.title)
    }

    private static func splitCode(_ value: String) -> (number: String?, title: String) {
        guard let number = HTMLRegex.firstCapture("^([A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*\\d+[A-Z]*|GTCNEURO)\\s+", in: value),
              let title = HTMLRegex.firstCapture("^(?:[A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*\\d+[A-Z]*|GTCNEURO)\\s+(.+)$", in: value) else {
            return (nil, value.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        return (number, title.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    private static func examTitle(from scheduleText: String?) -> String? {
        guard var value = scheduleText?.trimmedOrNil else {
            return nil
        }
        value = value.replacingOccurrences(
            of: #"^\d+\.\s*Parallelgruppe\s+"#,
            with: "",
            options: .regularExpression
        )
        value = value.replacingOccurrences(
            of: #"\s+(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+\d{2}\.\d{2}\.\d{2}\b.*$"#,
            with: "",
            options: .regularExpression
        )
        value = value.replacingOccurrences(
            of: #"\s+(Keine Uhrzeit festgelegt|Prüfungsform:|Prüfer/-in:).*$"#,
            with: "",
            options: .regularExpression
        )
        return value.trimmedOrNil
    }

    private static func scheduleText(from cells: [String]) -> String? {
        let source = cells.first {
            !$0.contains("Ihr aktueller Status:")
                && (
                    $0.contains("Parallelgruppe")
                    || $0.contains("Prüfungsform:")
                    || HTMLRegex.firstCapture("\\b\\d{2}\\.\\d{2}\\.\\d{2}\\b", in: $0) != nil
                )
        }
            ?? cells.first
        return source?
            .replacingOccurrences(
                of: "\\b(Status|Aktionen|Details anzeigen|Informationen zu Belegzeiträumen|Ab-/Ummelden)\\b",
                with: " ",
                options: .regularExpression
            )
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmedOrNil
    }

    private static func value(after label: String, in text: String) -> String? {
        let escaped = NSRegularExpression.escapedPattern(for: label)
        let pattern = "\(escaped):\\s*([^:]+?)(?=\\s+[A-ZÄÖÜ][^:]+:|$)"
        return HTMLRegex.firstCapture(pattern, in: text)?.trimmedOrNil
    }

    private static func detailURL(in table: String) -> String? {
        HTMLRegex.matches("<a\\b[^>]*>", in: table).compactMap { match -> String? in
            guard let range = Range(match.range, in: table) else {
                return nil
            }
            let tag = String(table[range])
            let href = HTMLRegex.attribute("href", in: tag)
            return href?.contains("_flowId=detailView-flow") == true ? href : nil
        }.first
    }

    private static func personName(in html: String) -> String? {
        for heading in blocks(named: "h2", in: html) {
            let text = HTMLText.stripTags(heading)
            guard text.localizedCaseInsensitiveContains("Personendaten:") else {
                continue
            }

            let cleaned = text
                .replacingOccurrences(of: "Personendaten:", with: "")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            return cleaned.isEmpty ? nil : cleaned
        }
        return nil
    }

    private static func fieldText(in row: String, suffixPattern: String) -> String? {
        let pattern = "<([A-Za-z][A-Za-z0-9]*)\\b[^>]*id\\s*=\\s*(['\"])[^'\"]*:\(suffixPattern)\\2[^>]*>(.*?)</\\1>"
        guard let raw = HTMLRegex.firstCapture(pattern, in: row, group: 3) else {
            return nil
        }
        let text = HTMLText.stripTags(raw)
        return text.isEmpty ? nil : text
    }

    private static func kindText(in row: String) -> String? {
        for match in HTMLRegex.matches("<img\\b[^>]*>", in: row) {
            guard let range = Range(match.range, in: row) else {
                continue
            }
            let tag = String(row[range])
            guard HTMLRegex.attribute("class", in: tag)?.contains("submitImageTable") == true else {
                continue
            }
            let alt = HTMLRegex.attribute("alt", in: tag)?.trimmingCharacters(in: .whitespacesAndNewlines)
            return alt?.isEmpty == false ? alt : nil
        }
        return nil
    }

    private static func firstTable(containingClass className: String, in html: String) -> String? {
        blocks(named: "table", in: html).first { table in
            openingTag(named: "table", in: table)
                .flatMap { HTMLRegex.attribute("class", in: $0) }?
                .components(separatedBy: .whitespacesAndNewlines)
                .contains(className) == true
        }
    }

    private static func block(named name: String, in html: String, attribute: String, value: String) -> String? {
        blocks(named: name, in: html).first { block in
            openingTag(named: name, in: block)
                .flatMap { HTMLRegex.attribute(attribute, in: $0) } == value
        }
    }

    private static func blocks(named name: String, in html: String) -> [String] {
        HTMLRegex.matches("<\(name)\\b[^>]*>.*?</\(name)>", in: html).compactMap { match in
            Range(match.range, in: html).map { String(html[$0]) }
        }
    }

    private static func nextBlock(named name: String, in html: String) -> String? {
        HTMLRegex.firstCapture("(<\(name)\\b[^>]*>.*?</\(name)>)", in: html)
    }

    private static func optionTags(in select: String) -> [String] {
        HTMLRegex.matches("<option\\b[^>]*>.*?</option>", in: select).compactMap { match in
            Range(match.range, in: select).map { String(select[$0]) }
        }
    }

    private static func openingTag(named name: String, in block: String) -> String? {
        HTMLRegex.firstCapture("(<\(name)\\b[^>]*>)", in: block)
    }
}
