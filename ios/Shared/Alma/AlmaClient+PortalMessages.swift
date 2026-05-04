import Foundation

extension AlmaClient {
    func fetchPortalMessages(credentials: AlmaCredentials) async throws -> AlmaPortalMessagesPage {
        try await login(credentials: credentials)
        let startPageURL = baseURL.appending(path: "alma/pages/cs/sys/portal/hisinoneStartPage.faces")
        let startPage = try await loadAuthenticatedHTMLResponse(startPageURL, pageName: "start page")
        let page = AlmaPortalMessagesHTMLParser.parsePage(startPage.html, pageURL: startPage.url)
        if !page.items.isEmpty {
            return page
        }

        let contract = try AlmaPortalMessagesHTMLParser.extractListContract(
            from: startPage.html,
            pageURL: startPage.url
        )
        guard var request = AlmaPortalMessagesHTMLParser.buildExpandRequest(contract) else {
            return page
        }
        request.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        let response = try await loadHTMLResponse(request)
        if AlmaHTMLParser.looksLoggedOut(response.html) {
            throw AlmaClientError.loginFailed("Session is not authenticated; the Alma start page redirected back to login.")
        }
        return try AlmaPortalMessagesHTMLParser.parsePartialResponse(response.html, pageURL: response.url)
    }
}
