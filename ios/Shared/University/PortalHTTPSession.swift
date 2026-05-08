import Foundation

struct PortalHTTPResponse {
    var data: Data
    var text: String
    var url: URL
}

struct PortalHTTPSession {
    private let session: URLSession
    private let userAgent: String

    init(userAgent: String) {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.httpCookieAcceptPolicy = .always
        configuration.httpShouldSetCookies = true
        self.init(session: URLSession(configuration: configuration), userAgent: userAgent)
    }

    init(session: URLSession, userAgent: String) {
        self.session = session
        self.userAgent = userAgent
    }

    func get(_ url: URL, headers: [String: String] = [:]) async throws -> PortalHTTPResponse {
        var request = URLRequest(url: url)
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        for (name, value) in headers {
            request.setValue(value, forHTTPHeaderField: name)
        }
        return try await load(request)
    }

    func postForm(_ form: UniversityHTMLForm) async throws -> PortalHTTPResponse {
        var request = URLRequest(url: form.actionURL)
        request.httpMethod = "POST"
        request.httpBody = HTTPFormEncoder.encode(form.payload)
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        return try await load(request)
    }

    func postJSON(_ body: Any, to url: URL, referer: URL?) async throws -> PortalHTTPResponse {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        if let referer {
            request.setValue(referer.absoluteString, forHTTPHeaderField: "Referer")
        }
        return try await load(request)
    }

    private func load(_ request: URLRequest) async throws -> PortalHTTPResponse {
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw UniversityPortalError.portal("The portal did not return an HTTP response.")
        }
        guard (200..<400).contains(http.statusCode) else {
            throw UniversityPortalError.portal("The portal request failed with HTTP \(http.statusCode).")
        }
        guard let finalURL = http.url ?? request.url else {
            throw UniversityPortalError.portal("The portal response did not include a final URL.")
        }
        let text = String(data: data, encoding: .utf8)
            ?? String(data: data, encoding: .isoLatin1)
            ?? String(decoding: data, as: UTF8.self)
        return PortalHTTPResponse(data: data, text: text, url: finalURL)
    }
}
