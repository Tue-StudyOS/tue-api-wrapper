import Foundation

struct AlmaPreparedDocument {
    let form: AlmaDocumentForm
    let previousLinks: Set<URL>

    var terms: [AlmaDocumentOption] { form.terms }
}

enum AlmaDocumentPreparation {
    case ready(Data)
    case choose(AlmaPreparedDocument)
}

struct AlmaDocumentSession {
    let client: AlmaClient

    static let officialURL = studyServiceURL(base: AlmaClient.officialBaseURL)

    func reports(credentials: AlmaCredentials) async throws -> [AlmaDocumentOption] {
        try await listing(credentials: credentials).form.reports
    }

    func prepare(_ report: AlmaDocumentOption, credentials: AlmaCredentials) async throws -> AlmaDocumentPreparation {
        let (form, previousLinks) = try await listing(credentials: credentials)
        guard form.reports.contains(report) else {
            throw AlmaDocumentError.unavailable("Alma no longer lists this report. Refresh the list and choose it again.")
        }

        let response = try await post(report, in: form, value: "")
        if let data = try await document(from: response, excluding: previousLinks) {
            return .ready(data)
        }
        let setup = try AlmaDocumentForm.parse(response.html, at: response.url)
        guard setup.start != nil, setup.termField == nil || !setup.terms.isEmpty else {
            throw AlmaDocumentError.unavailable("Alma did not expose the controls needed to prepare this report.")
        }
        return .choose(AlmaPreparedDocument(form: setup, previousLinks: previousLinks))
    }

    func download(_ prepared: AlmaPreparedDocument, term: AlmaDocumentOption?) async throws -> Data {
        let form = prepared.form
        guard let start = form.start else {
            throw AlmaDocumentError.unavailable("Alma did not offer a PDF creation action.")
        }
        var extra: [String: String] = [:]
        if let field = form.termField {
            guard let term, form.terms.contains(term) else {
                throw AlmaDocumentError.unavailable("Choose a semester offered by Alma.")
            }
            extra[field] = term.id
        }

        var response = try await post(start, in: form, value: start.title, extra: extra)
        for attempt in 0...6 {
            if let data = try await document(from: response, excluding: prepared.previousLinks) {
                return data
            }
            guard attempt < 6 else { break }
            let pollForm = try AlmaDocumentForm.parse(response.html, at: response.url)
            guard let poll = pollForm.poll else { break }
            try await Task.sleep(for: .seconds(1))
            response = try await post(poll, in: pollForm, value: poll.title)
        }
        throw AlmaDocumentError.unavailable("Alma did not return the generated PDF. Check Study Service for the report.")
    }

    private func listing(credentials: AlmaCredentials) async throws -> (form: AlmaDocumentForm, previousLinks: Set<URL>) {
        try await client.login(credentials: credentials)
        var response = try await request(URLRequest(url: Self.studyServiceURL(base: client.baseURL)))
        var form = try AlmaDocumentForm.parse(response.html, at: response.url)
        var links = Set(AlmaDocumentsHTML.downloadLinks(response.html, at: response.url))
        if form.reports.isEmpty, let tab = form.documentsTab {
            response = try await post(
                tab, in: form,
                value: tab.title.replacingOccurrences(of: "Aktive Registerkarte", with: "")
                    .trimmingCharacters(in: .whitespacesAndNewlines),
                extra: ["studyserviceForm:_idcl": tab.id, "DISABLE_VALIDATION": "true", "DISABLE_AUTOSCROLL": "true"]
            )
            form = try AlmaDocumentForm.parse(response.html, at: response.url)
            links.formUnion(AlmaDocumentsHTML.downloadLinks(response.html, at: response.url))
        }
        return (form, links)
    }

    private func post(
        _ action: AlmaDocumentOption, in form: AlmaDocumentForm, value: String, extra: [String: String] = [:]
    ) async throws -> Response {
        var fields = form.fields.merging(extra) { _, new in new }
        fields["activePageElementId"] = action.id
        fields["refreshButtonClickedId"] = ""
        fields[action.id] = value
        var next = URLRequest(url: form.action)
        next.httpMethod = "POST"
        next.httpBody = HTTPFormEncoder.encode(fields)
        next.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        return try await request(next)
    }

    private func document(from response: Response, excluding previousLinks: Set<URL>) async throws -> Data? {
        if response.isPDF { return response.data }
        let links = Set(AlmaDocumentsHTML.downloadLinks(response.html, at: response.url)).subtracting(previousLinks)
        guard !links.isEmpty else { return nil }
        guard links.count == 1, let link = links.first else {
            throw AlmaDocumentError.unavailable("Alma returned more than one new download. Choose your report in Study Service.")
        }
        let download = try await request(URLRequest(url: link))
        guard download.isPDF else {
            throw AlmaDocumentError.unavailable("The Alma download was not a PDF.")
        }
        return download.data
    }

    private func request(_ request: URLRequest) async throws -> Response {
        guard let url = request.url, isAlmaOrigin(url) else {
            throw AlmaDocumentError.unavailable("Alma returned a document action outside its configured address.")
        }
        var request = request
        request.setValue(client.userAgent, forHTTPHeaderField: "User-Agent")
        let (data, response) = try await client.session.data(for: request, delegate: AlmaRedirectGuard(origin: client.baseURL))
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode),
              let url = http.url, isAlmaOrigin(url) else {
            throw AlmaDocumentError.unavailable("Alma could not complete the document request.")
        }
        let result = Response(data: data, url: url)
        if !result.isPDF && AlmaHTMLParser.looksLoggedOut(result.html) {
            throw AlmaClientError.loginFailed("Alma asked you to sign in again.")
        }
        return result
    }

    private func isAlmaOrigin(_ url: URL) -> Bool {
        AlmaRedirectGuard.matches(url, origin: client.baseURL)
    }

    private static func studyServiceURL(base: URL) -> URL {
        base.appending(path: "alma/pages/cm/exa/enrollment/info/start.xhtml")
            .appending(queryItems: [
                URLQueryItem(name: "_flowId", value: "studyservice-flow"),
                URLQueryItem(name: "navigationPosition", value: "hisinoneMeinStudium,hisinoneStudyservice"),
                URLQueryItem(name: "recordRequest", value: "true")
            ])
    }

    private struct Response {
        let data: Data
        let url: URL
        var isPDF: Bool { data.starts(with: Data("%PDF-".utf8)) }
        var html: String { String(data: data, encoding: .utf8) ?? String(decoding: data, as: UTF8.self) }
    }
}
