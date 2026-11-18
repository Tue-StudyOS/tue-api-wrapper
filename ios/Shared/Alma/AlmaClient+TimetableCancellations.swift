import Foundation

extension AlmaClient {
    func timetableCancellations(
        from start: Date,
        to end: Date,
        page: (html: String, url: URL)
    ) async throws -> [LectureEvent] {
        let parser = AlmaTimetableCancellationHTMLParser.self
        let calendar = ICSDateParser.calendar()
        let first = calendar.startOfDay(for: start)
        let last = calendar.startOfDay(for: end)
        guard first <= last else { return [] }
        let visibleDays = parser.visibleDays(in: page.html)
        if let firstVisible = visibleDays.first, let lastVisible = visibleDays.last,
           firstVisible <= first, last <= lastVisible {
            return parser.cancellations(in: page.html)
        }

        var rangePage = page
        if let form = AlmaCourseRegistrationHTMLFormSupport.form(named: "plan", in: page.html),
           !hasRangeFields(in: form.body) {
            rangePage = try await selectTimetableDisplay(
                page, trigger: ":refreshAuswahlZeitraum",
                fields: [":auswahl_zeitraum_input": "zeitraum"],
                skipValidation: true
            )
        }

        let formatter = parser.dateFormatter("dd.MM.yyyy")
        var cancellations: [LectureEvent] = []
        var from = first
        // Alma accepts at most 20 day columns in a date range.
        while from <= last {
            guard let maximum = calendar.date(byAdding: .day, value: 19, to: from) else {
                throw AlmaClientError.timetableMissing("Could not calculate the timetable date range.")
            }
            let through = min(maximum, last)
            rangePage = try await selectTimetableDisplay(
                rangePage, trigger: ":anzeigeoptionen:anzeigeAktualisieren",
                fields: [":from": formatter.string(from: from), ":to": formatter.string(from: through)]
            )
            let days = parser.visibleDays(in: rangePage.html)
            guard days.first == from, days.last == through else {
                throw AlmaClientError.timetableMissing("Alma did not display the requested timetable date range.")
            }
            cancellations.append(contentsOf: parser.cancellations(in: rangePage.html))
            if through == last { break }
            guard let next = calendar.date(byAdding: .day, value: 1, to: through) else {
                throw AlmaClientError.timetableMissing("Could not advance the timetable date range.")
            }
            from = next
        }
        return cancellations
    }

    private func hasRangeFields(in html: String) -> Bool {
        HTMLRegex.firstCapture(#"\bname\s*=\s*['"]([^'"]*:anzeigeoptionen:from)['"]"#, in: html) != nil
    }

    private func selectTimetableDisplay(
        _ page: (html: String, url: URL),
        trigger: String,
        fields: [String: String],
        skipValidation: Bool = false
    ) async throws -> (html: String, url: URL) {
        let forms = AlmaCourseRegistrationHTMLFormSupport.self
        guard let form = forms.form(named: "plan", in: page.html),
              let action = HTMLRegex.attribute("action", in: form.tag),
              let url = URL(string: action, relativeTo: page.url)?.absoluteURL else {
            throw AlmaClientError.timetableMissing("Could not find the Alma timetable display form.")
        }
        let escaped = NSRegularExpression.escapedPattern(for: trigger)
        let pattern = "<button\\b[^>]*\\bname\\s*=\\s*['\"]([^'\"]*\(escaped))['\"][^>]*>"
        guard let button = HTMLRegex.firstCapture("(\(pattern))", in: form.body),
              let name = HTMLRegex.attribute("name", in: button) else {
            throw AlmaClientError.timetableMissing("Could not find the Alma timetable display control.")
        }

        var payload = forms.formPayload(in: form.body)
        for (suffix, value) in fields {
            guard let key = payload.keys.first(where: { $0.hasSuffix(suffix) }) else {
                throw AlmaClientError.timetableMissing("Alma is missing a required timetable display field.")
            }
            payload[key] = value
        }
        payload[name] = HTMLRegex.attribute("value", in: button) ?? ""
        payload["activePageElementId"] = name
        payload["refreshButtonClickedId"] = name
        if skipValidation { payload["DISABLE_VALIDATION"] = "true" }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = HTTPFormEncoder.encode(payload)
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        return try await loadHTMLResponse(request)
    }
}
