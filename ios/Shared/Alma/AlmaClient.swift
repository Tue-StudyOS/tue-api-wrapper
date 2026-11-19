import Foundation

struct AlmaClient {
    static let officialBaseURL = URL(string: "https://alma.uni-tuebingen.de")!
    let baseURL: URL
    let session: URLSession

    init(baseURL: URL) {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.httpCookieAcceptPolicy = .always
        configuration.httpShouldSetCookies = true
        self.init(baseURL: baseURL, session: URLSession(configuration: configuration))
    }

    init(baseURL: URL, session: URLSession) {
        self.baseURL = baseURL
        self.session = session
    }

    func fetchUpcomingLectures(
        credentials: AlmaCredentials,
        days: Int = 14,
        limit: Int = 32
    ) async throws -> LectureSnapshot {
        try await login(credentials: credentials)
        let page = try await loadAuthenticatedHTMLResponse(timetableURL(), pageName: "timetable page")
        let enrollment = try await loadAuthenticatedHTMLResponse(
            enrollmentURL(),
            pageName: "enrollment page"
        )
        let enrollmentState = try AlmaAcademicHTMLParser.parseEnrollment(enrollment.html)
        let terms = try AlmaHTMLParser.extractTerms(from: page.html)
        guard let term = terms.first(where: \.isSelected) ?? terms.first else {
            throw AlmaClientError.timetableMissing("Could not determine the selected Alma term.")
        }

        let exportURL = try buildExportURL(from: AlmaHTMLParser.extractExportURL(from: page.html), termID: term.value)
        let rawICS = try await loadText(exportURL)
        guard rawICS.contains("BEGIN:VCALENDAR") else {
            throw AlmaClientError.timetableMissing("Expected an iCalendar export but received a different response.")
        }

        let now = Date()
        let calendar = ICSDateParser.calendar()
        let end = calendar.date(byAdding: .day, value: days, to: now) ?? now
        let events = try ICSEventParser.parse(rawICS)
        let lectures = try RecurrenceExpander.expand(events, from: now, to: end)
        let enrichedLectures = AlmaTimetableRoomHTMLParser.enrich(lectures, html: page.html, pageURL: page.url)
        let dayStart = calendar.startOfDay(for: now)
        let cancellations = try await timetableCancellations(from: dayStart, to: end, page: page)
        let visibleCancellations = cancellations.filter { dayStart <= $0.startDate && $0.startDate <= end }
        let timetable = AlmaTimetableCancellationHTMLParser.merge(enrichedLectures, with: visibleCancellations)

        return LectureSnapshot(
            refreshedAt: now,
            sourceTerm: term.label,
            events: Array(timetable.prefix(limit)),
            semesterCredits: SemesterCreditCounter.summarize(events),
            personName: enrollmentState.personName
        )
    }

    func fetchCurrentLectures(
        date: String? = nil,
        limit: Int = 100,
        credentials: AlmaCredentials? = nil
    ) async throws -> AlmaCurrentLecturesPage {
        if let credentials {
            try await login(credentials: credentials)
        }

        var response = try await loadHTMLResponse(currentLecturesURL())

        if let date, !date.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            let form = try AlmaCurrentLecturesParser.extractForm(from: response.html, pageURL: response.url)
            var payload = form.payload
            payload.append((form.dateFieldName, date))
            if let filterName = form.filterFieldName {
                for value in form.filterValues {
                    payload.append((filterName, value))
                }
            }
            payload.append(("activePageElementId", form.searchButtonName))
            payload.append((form.searchButtonName, "Suchen"))

            var request = URLRequest(url: form.actionURL)
            request.httpMethod = "POST"
            request.httpBody = HTTPFormEncoder.encode(payload)
            request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
            response = try await loadHTMLResponse(request)
        }

        let page = try AlmaCurrentLecturesParser.parsePage(response.html, pageURL: response.url)
        return AlmaCurrentLecturesPage(
            pageURL: page.pageURL,
            selectedDate: page.selectedDate,
            results: Array(page.results.prefix(max(1, limit)))
        )
    }

    func fetchAcademicOverview(
        credentials: AlmaCredentials,
        examLimit: Int = 50
    ) async throws -> AlmaAcademicOverview {
        try await login(credentials: credentials)

        let enrollment = try await loadAuthenticatedHTMLResponse(
            enrollmentURL(),
            pageName: "enrollment page"
        )
        let exams = try await loadAuthenticatedHTMLResponse(
            examOverviewURL(),
            pageName: "exam overview page"
        )

        return AlmaAcademicOverview(
            enrollment: try AlmaAcademicHTMLParser.parseEnrollment(enrollment.html),
            exams: try AlmaAcademicHTMLParser.parseExamOverview(exams.html, limit: examLimit)
        )
    }

    func login(credentials: AlmaCredentials) async throws {
        let response = try await loadHTMLResponse(startPageURL())
        var form = try AlmaHTMLParser.extractLoginForm(from: response.html, pageURL: response.url)
        form.payload["asdf"] = credentials.username
        form.payload["fdsa"] = credentials.password
        form.payload["submit", default: ""] = ""

        var request = URLRequest(url: form.actionURL)
        request.httpMethod = "POST"
        request.httpBody = HTTPFormEncoder.encode(form.payload)
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")

        let login = try await loadHTMLResponse(request)
        if AlmaHTMLParser.looksLoggedOut(login.html) {
            let message = AlmaHTMLParser.extractLoginError(from: login.html) ?? "Alma login did not reach an authenticated page."
            throw AlmaClientError.loginFailed(message)
        }
    }

    private func loadText(_ url: URL) async throws -> String {
        try await loadHTMLResponse(url).html
    }

    func loadAuthenticatedHTMLResponse(
        _ url: URL,
        pageName: String
    ) async throws -> (html: String, url: URL) {
        let response = try await loadHTMLResponse(url)
        if AlmaHTMLParser.looksLoggedOut(response.html) {
            throw AlmaClientError.loginFailed("Session is not authenticated; the \(pageName) redirected back to login.")
        }
        return response
    }

    func loadHTMLResponse(_ url: URL) async throws -> (html: String, url: URL) {
        var request = URLRequest(url: url)
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        return try await loadHTMLResponse(request)
    }

    func loadHTMLResponse(_ request: URLRequest) async throws -> (html: String, url: URL) {
        guard let url = request.url, AlmaRedirectGuard.matches(url, origin: baseURL) else {
            throw AlmaClientError.server("Alma provided a link outside its official connection.")
        }
        let (data, response) = try await session.data(for: request, delegate: AlmaRedirectGuard(origin: baseURL))
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AlmaClientError.server("Alma did not return an HTTP response.")
        }
        guard (200..<300).contains(httpResponse.statusCode) else {
            throw AlmaClientError.server("Alma request failed with HTTP \(httpResponse.statusCode).")
        }
        guard let finalURL = httpResponse.url ?? request.url else {
            throw AlmaClientError.server("Alma response did not include a final URL.")
        }
        let html = String(data: data, encoding: .utf8)
            ?? String(data: data, encoding: .isoLatin1)
            ?? String(decoding: data, as: UTF8.self)
        return (html, finalURL)
    }

    private func startPageURL() -> URL {
        baseURL.appending(path: "alma/pages/cs/sys/portal/hisinoneStartPage.faces")
    }

    private func timetableURL() -> URL {
        baseURL.appending(path: "alma/pages/plan/individualTimetable.xhtml")
            .appending(queryItems: [
                URLQueryItem(name: "_flowId", value: "individualTimetableSchedule-flow"),
                URLQueryItem(name: "navigationPosition", value: "hisinoneMeinStudium,individualTimetableSchedule"),
                URLQueryItem(name: "recordRequest", value: "true")
            ])
    }

    private func currentLecturesURL() -> URL {
        baseURL.appending(path: "alma/pages/cm/exa/timetable/currentLectures.xhtml")
            .appending(queryItems: [
                URLQueryItem(name: "_flowId", value: "showEventsAndExaminationsOnDate-flow"),
                URLQueryItem(name: "navigationPosition", value: "studiesOffered,currentLecturesGeneric"),
                URLQueryItem(name: "recordRequest", value: "true")
            ])
    }

    private func enrollmentURL() -> URL {
        baseURL.appending(path: "alma/pages/cm/exa/enrollment/info/start.xhtml")
            .appending(queryItems: [
                URLQueryItem(name: "_flowId", value: "searchOwnEnrollmentInfo-flow"),
                URLQueryItem(name: "navigationPosition", value: "hisinoneMeinStudium,hisinoneOwnEnrollmentList"),
                URLQueryItem(name: "recordRequest", value: "true")
            ])
    }

    private func examOverviewURL() -> URL {
        baseURL.appending(path: "alma/pages/sul/examAssessment/personExamsReadonly.xhtml")
            .appending(queryItems: [
                URLQueryItem(name: "_flowId", value: "examsOverviewForPerson-flow"),
                URLQueryItem(name: "navigationPosition", value: "hisinoneMeinStudium,examAssessmentForStudent"),
                URLQueryItem(name: "recordRequest", value: "true")
            ])
    }

    private func buildExportURL(from rawURL: String, termID: String) throws -> URL {
        let absoluteURL = URL(string: rawURL, relativeTo: baseURL)?.absoluteString ?? rawURL
        guard var components = URLComponents(string: absoluteURL) else {
            throw AlmaClientError.timetableMissing("The Alma iCalendar export URL was invalid.")
        }
        var items = components.queryItems ?? []
        items.removeAll { $0.name == "termgroup" }
        items.append(URLQueryItem(name: "termgroup", value: termID))
        components.queryItems = items
        guard let url = components.url else {
            throw AlmaClientError.timetableMissing("Could not build a term-specific iCalendar export URL.")
        }
        return url
    }

    var userAgent: String {
        "tue-api-wrapper-ios/0.1 (+https://alma.uni-tuebingen.de/)"
    }
}
