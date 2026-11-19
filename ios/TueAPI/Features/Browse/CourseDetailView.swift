import SwiftUI

struct CourseDetailView: View {
    var model: AppModel
    var course: CourseDetailReference
    var event: LectureEvent?
    @AppStorage(StudentCourseLinks.storageKey) private var linksData = Data()
    @State private var portalStatusPhase: PortalStatusPhase = .idle

    init(lecture: AlmaCurrentLecture, model: AppModel) {
        self.model = model
        self.course = CourseDetailReference(lecture: lecture)
    }

    init(event: LectureEvent, model: AppModel) {
        self.model = model
        self.course = CourseDetailReference(event: event)
        self.event = event
    }

    var body: some View {
        List {
            StudentListHeading(title: course.title, detail: subtitle)
            if course.number != nil || course.semester != nil {
                Section("Course information") {
                    if let number = course.number {
                        LabeledContent("Course number", value: number)
                    }
                    if let semester = course.semester {
                        LabeledContent("Semester", value: semester)
                    }
                }
            }

            if let timeRange = course.timeRange {
                Section("Schedule") {
                    LabeledContent("Time", value: timeRange)
                    if let event, !event.isCancelled, (event.endDate ?? event.startDate) > Date() {
                        Button("Start lecture Live Activity") { model.startLiveActivity(for: event) }
                        if let message = model.liveActivityMessage {
                            Text(message).font(.footnote).foregroundStyle(.secondary)
                        }
                    }
                    if course.scheduleStatus == .cancelled {
                        Label("Canceled", systemImage: "calendar.badge.minus")
                        if let reason = course.cancellationReason {
                            Text(reason)
                        }
                    }
                }
            }

            Section("Alma signup status") {
                portalStatusContent
            }

            CourseCriticalActionsView(model: model, course: course)

            if course.location?.nilIfEmpty != nil {
                Section("Quick navigation") {
                    CourseNavigationActions(course: course)
                }
            }

            Section("Materials and course pages") {
                if let detailURL = course.detailURL {
                    Link(destination: detailURL) {
                        Label("Open Alma detail", systemImage: "rectangle.portrait.and.arrow.right")
                    }
                }
                if let iliasURL = course.iliasURL {
                    Link(destination: iliasURL) {
                        Label("Open ILIAS space", systemImage: "book.pages")
                    }
                }
                if let searchURL = iliasSearchURL {
                    Link(destination: searchURL) {
                        Label(iliasSearchLabel, systemImage: "magnifyingglass")
                    }
                }
                if let iliasQuery {
                    LabeledContent("ILIAS query", value: iliasQuery)
                }
            }

            if let detailURL = course.detailURL, model.hasCredentials {
                StudentCourseLinks(almaURL: detailURL, sourceCourse: course.iliasURL, candidates: model.iliasAssignments)
            }
            if let iliasURL = effectiveIliasURL {
                CourseIliasAssignmentsSection(target: iliasURL, credentialsLoader: model.keychain)
                    .id(iliasURL)
            }

            Section("Teaching") {
                if let eventType = course.eventType {
                    LabeledContent("Type", value: eventType)
                }
                if let lecturer = course.lecturer {
                    LabeledContent("Lecturer", value: lecturer)
                }
                if let location = course.location {
                    LabeledContent("Location", value: location)
                }
                if let remark = course.remark {
                    Text(remark)
                        .font(.subheadline)
                }
                if course.eventType == nil, course.lecturer == nil, course.location == nil, course.remark == nil {
                    Text("No teaching metadata is available for this calendar entry.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            if let sourceDetail = course.sourceDetail {
                Section("Alma calendar detail") {
                    Text(sourceDetail)
                        .font(.subheadline)
                }
            }
        }
        .navigationTitle("Course")
        .navigationBarTitleDisplayMode(.inline)
        .task(id: statusLookupID) {
            await loadPortalStatuses()
        }
    }

    private var effectiveIliasURL: URL? {
        if let sourceURL = course.iliasURL { return sourceURL }
        guard model.hasCredentials, let detailURL = course.detailURL,
              let links = try? JSONDecoder().decode([String: String].self, from: linksData),
              let value = links[detailURL.absoluteString] else { return nil }
        return URL(string: value)
    }

    private var subtitle: String? {
        [course.eventType, course.lecturer]
            .compactMap { $0 }
            .joined(separator: " · ")
            .nilIfEmpty
    }

    private var iliasQuery: String? {
        (course.number ?? course.title).nilIfEmpty
    }

    private var iliasSearchLabel: String {
        course.number == nil ? "Search ILIAS by title" : "Search ILIAS by course code"
    }

    private var iliasSearchURL: URL? {
        guard let iliasQuery else { return nil }
        var components = URLComponents()
        components.scheme = "https"
        components.host = "ovidius.uni-tuebingen.de"
        components.path = "/ilias.php"
        components.queryItems = [
            URLQueryItem(name: "baseClass", value: "ilSearchControllerGUI"),
            URLQueryItem(name: "term", value: iliasQuery)
        ]
        return components.url
    }

    @ViewBuilder
    private var portalStatusContent: some View {
        switch portalStatusPhase {
        case .idle, .loading:
            ProgressView("Loading Alma signup status")
        case .unavailable(let message):
            StatusBanner(title: "Status lookup unavailable", message: message, systemImage: "network.slash")
        case .failed(let message):
            StatusBanner(title: "Status lookup failed", message: message, systemImage: "exclamationmark.triangle")
        case .loaded(let statuses):
            if statuses.isEmpty {
                Text("No portal status was returned.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(statuses) { status in
                    PortalStatusRow(status: status)
                }
            }
        }
    }

    private var statusLookupID: String {
        [
            course.id,
            course.detailURL?.absoluteString ?? "",
            course.title
        ].joined(separator: "|")
    }

    private func loadPortalStatuses() async {
        guard let detailURL = course.detailURL else {
            portalStatusPhase = .unavailable("This course entry does not expose an Alma detail page, so signup status cannot be checked on-device.")
            return
        }

        portalStatusPhase = .loading
        do {
            let (client, credentials) = try model.almaAccessContext(for: "check Alma signup status")
            let support = try await client.inspectCourseRegistration(
                detailURL: detailURL,
                credentials: credentials
            )
            portalStatusPhase = .loaded([almaPortalStatus(from: support)])
        } catch {
            portalStatusPhase = .failed(error.localizedDescription)
        }
    }

    private func almaPortalStatus(from support: AlmaCourseRegistrationSupport) -> CoursePortalStatus {
        let signedUp: Bool?
        switch support.status {
        case "registered":
            signedUp = true
        case "not_registered":
            signedUp = false
        default:
            signedUp = nil
        }

        let status = support.status
            ?? (support.supported ? "registration_available" : "not_available")

        return CoursePortalStatus(
            portal: "alma",
            status: status,
            signedUp: signedUp,
            title: course.title,
            url: support.detailURL.absoluteString,
            matchReason: "Authenticated Alma detail page",
            score: support.supported ? 100 : nil,
            message: support.message ?? support.messages.first,
            error: nil
        )
    }
}

private extension String {
    var nilIfEmpty: String? {
        let value = trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? nil : value
    }
}
