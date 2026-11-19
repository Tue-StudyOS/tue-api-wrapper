import SwiftUI

struct OnboardingView: View {
    var model: AppModel
    @Binding var exploreWithoutAccount: Bool
    @Binding var finishingSetup: Bool
    @State private var showsSignIn = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                StudentScreenHeading(
                    title: "Your university in one place",
                    detail: "See your lectures, deadlines and official documents."
                )

                Button("Connect university account") {
                    showsSignIn = true
                }
                .studentProminentButton()
                .controlSize(.large)

                Button("Explore Campus without signing in") {
                    exploreWithoutAccount = true
                }
                .frame(minHeight: 44)
            }
            .frame(maxWidth: 480, alignment: .leading)
            .padding(24)
            .frame(maxWidth: .infinity)
        }
        .toolbar(.hidden, for: .navigationBar)
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationDestination(isPresented: $showsSignIn) {
            UniversityConnectionView(model: model, finishingSetup: $finishingSetup)
        }
    }
}

struct UniversityConnectionView: View {
    var model: AppModel
    @Binding var finishingSetup: Bool
    @State private var username = ""
    @State private var password = ""
    @State private var checks: [UniversityConnectionCheck] = []
    @State private var isChecking = false
    @State private var showSaveError = false

    var body: some View {
        Form {
            StudentListHeading(title: "Connect your account", detail: "Use your University of Tübingen login.")
            if !isChecking && checks.isEmpty {
                Section {
                    UniversityCredentialsFields(username: $username, password: $password)
                } footer: {
                    Text("Your login is stored in the Keychain on this device.")
                }
                Button("Connect services", action: connect)
                    .disabled(username.trimmedOrNil == nil || password.isEmpty)
                if showSaveError, case .failed(let message) = model.phase {
                    Label(message, systemImage: "exclamationmark.triangle")
                }
            } else {
                Section("Services") {
                    if isChecking {
                        ProgressView("Checking university services")
                    }
                    ForEach(checks) { check in
                        LabeledContent(check.service, value: check.status)
                    }
                }
                if !isChecking {
                    Button("Continue to Today") { finishingSetup = false }
                }
            }
        }
        .navigationTitle("Connect account")
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(finishingSetup)
        .task(id: isChecking) {
            guard isChecking else { return }
            checks = await UniversityConnectionCheck.fetch(using: model)
            guard !Task.isCancelled else { return }
            isChecking = false
        }
    }

    private func connect() {
        finishingSetup = true
        model.saveCredentials(username: username, password: password)
        guard model.hasCredentials else {
            finishingSetup = false
            showSaveError = true
            return
        }
        password = ""
        showSaveError = false
        isChecking = true
    }
}

private struct UniversityConnectionCheck: Identifiable {
    let service: String
    let status: String
    var id: String { service }

    @MainActor
    static func fetch(using model: AppModel) async -> [Self] {
        async let alma: Void = model.refreshUpcomingLectures()
        async let courses: Void = model.refreshTasks()
        _ = await (alma, courses)

        let almaStatus: String
        if case .loaded = model.phase { almaStatus = "Timetable checked" }
        else { almaStatus = "Could not check timetable" }

        let courseStatus: String
        switch model.tasksPhase {
        case .loaded:
            courseStatus = model.tasksWarning ?? "Deadlines checked"
        default:
            courseStatus = "Could not check deadlines"
        }
        return [
            Self(service: "Alma", status: almaStatus),
            Self(service: "Moodle and ILIAS", status: courseStatus)
        ]
    }
}
