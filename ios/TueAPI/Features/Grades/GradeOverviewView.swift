import SwiftUI

struct GradeOverviewView: View {
    var model: AppModel

    @Environment(\.openURL) private var openURL
    @State private var phase: GradeLoadPhase = .idle
    @State private var payload: GradeOverviewPayload?

    var body: some View {
        List {
            Section {
                statusContent
            }

            if let payload {
                summarySection(payload)
                almaSection(payload)
                moodleSection(payload.moodleGrades)
                enrollmentSection(payload.enrollment)
            } else if phase != .loading {
                Section {
                    ContentUnavailableView(
                        "Grades not loaded",
                        systemImage: "graduationcap",
                        description: Text("Refresh to load Alma exam records and Moodle grade rows.")
                    )
                }
            }
        }
        .navigationTitle("Grades")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refresh() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(phase.isLoading)
            }
        }
        .task {
            if payload == nil {
                await refresh()
            }
        }
        .refreshable {
            await refresh()
        }
    }

    @ViewBuilder
    private var statusContent: some View {
        switch phase {
        case .idle:
            StatusBanner(
                title: model.hasCredentials ? "On-device grades" : "Login required",
                message: model.hasCredentials
                    ? "Grades load from Alma and Moodle using the university login saved on this device."
                    : "Connect your university account in Settings to refresh grades.",
                systemImage: model.hasCredentials ? "lock.shield" : "key"
            )
        case .loading:
            ProgressView("Loading grades")
        case .loaded(let date):
            StatusBanner(
                title: "Grades refreshed",
                message: "Updated \(date.formatted(date: .abbreviated, time: .shortened)).",
                systemImage: "graduationcap"
            )
        case .unavailable:
            StatusBanner(
                title: "Alma unavailable",
                message: "The configured Alma base URL is not available in this build.",
                systemImage: "exclamationmark.triangle"
            )
        case .failed(let message):
            StatusBanner(title: "Grades unavailable", message: message, systemImage: "exclamationmark.triangle")
        }
    }

    private func summarySection(_ payload: GradeOverviewPayload) -> some View {
        let stats = GradeOverviewStats(exams: payload.exams)
        return Section("Summary") {
            LabeledContent("Selected term", value: payload.enrollment.selectedTerm ?? "-")
            LabeledContent("Passed exams", value: "\(stats.passedExamCount)")
            LabeledContent("Tracked credits", value: creditsText(stats.trackedCredits))
            LabeledContent("Graded records", value: "\(stats.graded.count)")
            LabeledContent("Pending records", value: "\(stats.pending.count)")
            LabeledContent("Belegungen", value: "\(payload.enrollment.entries.count)")
        }
    }

    @ViewBuilder
    private func almaSection(_ payload: GradeOverviewPayload) -> some View {
        let stats = GradeOverviewStats(exams: payload.exams)

        Section("Graded Alma records") {
            if stats.graded.isEmpty {
                ContentUnavailableView(
                    "No graded records",
                    systemImage: "doc.text.magnifyingglass",
                    description: Text("No Alma rows with explicit grades were visible.")
                )
            } else {
                ForEach(stats.graded) { exam in
                    GradeRecordRow(exam: exam)
                }
            }
        }

        Section("Pending Alma records") {
            if stats.pending.isEmpty {
                ContentUnavailableView(
                    "No pending records",
                    systemImage: "checkmark.circle",
                    description: Text("Every visible Alma row has an explicit grade.")
                )
            } else {
                ForEach(stats.pending) { exam in
                    GradeRecordRow(exam: exam)
                }
            }
        }
    }

    @ViewBuilder
    private func moodleSection(_ response: MoodleGradesResponse) -> some View {
        Section("Moodle grades") {
            if let url = URL(string: response.sourceURL) {
                Button {
                    openURL(url)
                } label: {
                    Label("Open Moodle grades", systemImage: "arrow.up.forward.square")
                }
            }

            if response.items.isEmpty {
                ContentUnavailableView(
                    "No Moodle grades",
                    systemImage: "graduationcap",
                    description: Text("No Moodle grade rows were visible for this account.")
                )
            } else {
                ForEach(response.items) { grade in
                    if let urlString = grade.url, let url = URL(string: urlString) {
                        Button {
                            openURL(url)
                        } label: {
                            MoodleGradeRow(grade: grade)
                        }
                        .buttonStyle(.plain)
                    } else {
                        MoodleGradeRow(grade: grade)
                    }
                }
            }
        }
    }

    private func enrollmentSection(_ enrollment: AlmaEnrollmentState) -> some View {
        Section("Belegungen") {
            if let message = enrollment.message?.trimmedOrNil {
                Text(message)
                    .font(.body)
                    .textSelection(.enabled)
            }

            if enrollment.entries.isEmpty {
                ContentUnavailableView(
                    "No Belegungen",
                    systemImage: "calendar.badge.exclamationmark",
                    description: Text("No Alma enrolment or exam-registration rows were visible for this term.")
                )
            } else {
                ForEach(enrollment.entries) { record in
                    EnrollmentRecordRow(record: record)
                }
            }
        }
    }

    private func refresh() async {
        guard let almaBaseURL = URL(string: model.baseURLString),
              ["http", "https"].contains(almaBaseURL.scheme?.lowercased() ?? "") else {
            phase = .unavailable
            return
        }

        phase = .loading
        do {
            let response = try await UniversityGradesClient(
                credentialsLoader: model.keychain,
                almaBaseURL: almaBaseURL
            )
            .fetchGrades(
                examLimit: 50,
                moodleLimit: 50
            )
            payload = response
            phase = .loaded(response.refreshedAt)
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func creditsText(_ value: Double) -> String {
        String(format: "%.1f", value)
    }
}
