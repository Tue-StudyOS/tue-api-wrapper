import Foundation

struct IliasOnDeviceClient: UniversityIliasTaskLoading {
    private let credentials: AlmaCredentials
    private let loginURL: URL
    private let http: PortalHTTPSession

    init(
        credentials: AlmaCredentials,
        loginURL: URL = URL(string: "https://ovidius.uni-tuebingen.de/login.php?cmd=force_login")!,
        http: PortalHTTPSession = PortalHTTPSession(userAgent: "tue-api-wrapper-ios/0.1 (+https://ovidius.uni-tuebingen.de/)")
    ) {
        self.credentials = credentials
        self.loginURL = loginURL
        self.http = http
    }

    func fetchTasks(limit: Int = 20) async throws -> [IliasTask] {
        try await login()
        let page = try await http.get(taskOverviewURL)
        return Array(try IliasTaskHTMLParser.parse(page.text, pageURL: page.url).prefix(max(1, limit)))
    }

    func fetchContent(target: String) async throws -> IliasContentPage {
        try await login()
        return try await fetchContentAfterLogin(target: target)
    }

    func fetchExerciseAssignments(target: String) async throws -> [IliasExerciseAssignment] {
        try await login()
        return try await fetchExerciseAssignmentsAfterLogin(target: target)
    }

    func fetchCourseAssignments(target: String) async throws -> IliasCourseAssignmentsPage {
        try await login()
        let course = try await fetchContentAfterLogin(target: target)
        var groups: [IliasCourseExerciseAssignments] = []
        for exercise in IliasCourseAssignmentsBuilder.exerciseItems(in: course) {
            let assignments = try await fetchExerciseAssignmentsAfterLogin(target: exercise.url)
            groups.append(IliasCourseExerciseAssignments(exercise: exercise, assignments: assignments))
        }
        return IliasCourseAssignmentsPage(course: course, exercises: groups)
    }

    private func login() async throws {
        let loginPage = try await http.get(loginURL)
        let shibbolethURL = try UniversityHTMLFormParser.linkURL(
            containing: "shib_login.php",
            in: loginPage.text,
            pageURL: loginPage.url
        )
        let idpPage = try await http.get(shibbolethURL)
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
            isAuthenticated: Self.isAuthenticatedIliasPage
        )
    }

    private var taskOverviewURL: URL {
        URL(string: "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilderivedtasksgui")!
    }

    private func fetchContentAfterLogin(target: String) async throws -> IliasContentPage {
        let page = try await http.get(try targetURL(target))
        return try IliasContentHTMLParser.parse(page.text, pageURL: page.url)
    }

    private func fetchExerciseAssignmentsAfterLogin(target: String) async throws -> [IliasExerciseAssignment] {
        let page = try await http.get(try targetURL(target))
        return try IliasExerciseAssignmentHTMLParser.parse(page.text, pageURL: page.url)
    }

    private func targetURL(_ target: String) throws -> URL {
        let trimmed = target.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            throw UniversityPortalError.invalidURL("A non-empty ILIAS target is required.")
        }
        if let url = URL(string: trimmed), url.scheme?.hasPrefix("http") == true {
            return url
        }
        if trimmed.hasPrefix("goto.php/"),
           let url = URL(string: trimmed, relativeTo: iliasBaseURL)?.absoluteURL {
            return url
        }
        let relative = trimmed.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: relative, relativeTo: iliasGotoBaseURL)?.absoluteURL else {
            throw UniversityPortalError.invalidURL("The ILIAS target could not be converted to a URL.")
        }
        return url
    }

    private static func isAuthenticatedIliasPage(_ response: PortalHTTPResponse) -> Bool {
        guard response.url.host == "ovidius.uni-tuebingen.de" else {
            return false
        }
        let html = response.text
        if loginOrHandoffMarkers.contains(where: html.contains) {
            return false
        }
        return authenticatedMarkers.contains(where: html.contains)
    }

    private static let authenticatedMarkers = [
        "ILIAS Universität Tübingen",
        "logout.php",
        "il-mainbar-entries",
        "il-maincontrols-metabar",
        "baseClass=ilDashboardGUI",
        "baseClass=ilmembershipoverviewgui",
        "baseClass=ilderivedtasksgui"
    ]

    private static let loginOrHandoffMarkers = [
        "SAML" + "Response",
        "j_username",
        "j_password",
        "Login mit zentraler Universitäts-Kennung"
    ]

    private let iliasBaseURL = URL(string: "https://ovidius.uni-tuebingen.de/")!
    private let iliasGotoBaseURL = URL(string: "https://ovidius.uni-tuebingen.de/goto.php/")!
}
