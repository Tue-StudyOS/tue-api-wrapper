import Foundation

struct PraxisportalOnDeviceClient {
    private let credentials: AlmaCredentials
    private let baseURL: URL
    private let http: PortalHTTPSession
    private let assertionFieldName = "SAML" + "Response"

    init(
        credentials: AlmaCredentials,
        baseURL: URL = URL(string: "https://www.praxisportal.uni-tuebingen.de")!,
        http: PortalHTTPSession = PortalHTTPSession(userAgent: "tue-api-wrapper-ios/0.1 (+https://www.praxisportal.uni-tuebingen.de/)")
    ) {
        self.credentials = credentials
        self.baseURL = baseURL
        self.http = http
    }

    func createSubscription(query: CareerSubscriptionQuery, subscriptionTypeId: Int = 1) async throws -> CareerSubscription {
        try await login()
        let payload = CareerSubscriptionCreatePayload(
            query: query,
            subscriptionTypeId: subscriptionTypeId
        )
        let response = try await http.postJSON(
            payload.jsonObject(),
            to: baseURL.appending(path: "1/subscription/create"),
            referer: baseURL.appending(path: "candidate/search")
        )
        return try JSONDecoder().decode(CareerSubscriptionCreateResponse.self, from: response.data).subscription
    }

    private func login() async throws {
        let loginURL = baseURL.appending(path: "shibboleth")
            .appending(queryItems: [URLQueryItem(name: "lang", value: "de")])
        let idpPage = try await http.get(loginURL)
        if isAuthenticatedPraxisportalPage(idpPage) {
            return
        }
        let form = try UniversityHTMLFormParser.idpLoginForm(
            in: idpPage.text,
            pageURL: idpPage.url
        ).applying(credentials: credentials)
        let submitted = try await http.postForm(form)
        if let error = UniversityHTMLFormParser.idpError(in: submitted.text) {
            throw UniversityPortalError.loginFailed(error)
        }
        _ = try await UniversitySAMLHandoff.complete(
            response: submitted,
            http: http,
            isAuthenticated: isAuthenticatedPraxisportalPage
        )
    }

    private func isAuthenticatedPraxisportalPage(_ response: PortalHTTPResponse) -> Bool {
        response.url.host == baseURL.host
            && !response.text.contains("j_username")
            && !response.text.contains(assertionFieldName)
    }
}

private struct CareerSubscriptionCreatePayload {
    var query: CareerSubscriptionQuery
    var subscriptionTypeId: Int

    func jsonObject() -> [String: Any] {
        [
            "query": [
                "in_english": query.inEnglish,
                "start_date": query.startDate ?? "",
                "end_date": query.endDate ?? "",
                "text": query.text,
                "industries": query.industries,
                "project_subtypes": query.projectSubtypes,
                "postal_code": query.postalCode,
                "project_type_id": query.projectTypeId,
                "version": query.version
            ],
            "subscription_type_id": subscriptionTypeId
        ]
    }
}

private struct CareerSubscriptionCreateResponse: Decodable {
    var success: Bool
    var subscription: CareerSubscription
}
