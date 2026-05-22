import SwiftUI

struct SettingsView: View {
    @Bindable var model: AppModel
    @State private var username = ""
    @State private var password = ""
    @State private var activeSheet: SettingsSheet?
    @State private var feedbackEnabled = false

    var body: some View {
        Form {
            Section("University login") {
                UniversityCredentialsFields(
                    username: $username,
                    password: $password
                )
            }

            Section {
                Button("Save login") {
                    model.saveCredentials(username: username, password: password)
                    password = ""
                }
                .disabled(username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || password.isEmpty)

                if model.hasCredentials {
                    Button("Remove login", role: .destructive) {
                        model.deleteCredentials()
                        password = ""
                    }
                }
            }

            Section {
                StatusBanner(
                    title: model.hasCredentials ? "University account connected" : "University account not connected",
                    message: model.hasCredentials ? "Study Hub can refresh Alma, Moodle, ILIAS, and mail on this device. Widgets only read cached lecture data." : "Connect your account to sync your timetable, tasks, grades, and university mail.",
                    systemImage: model.hasCredentials ? "lock.shield" : "lock"
                )
            }

            Section {
                TextField("Base URL", text: $model.baseURLString)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
            } header: {
                Text("Alma connection")
            } footer: {
                Text("Default Alma address: https://alma.uni-tuebingen.de.")
            }

            Section("Widget cache") {
                Text("Upcoming lectures are cached in the app group after each refresh.")
                Text(AppGroup.identifier)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Section("Assistant") {
                NavigationLink {
                    StudyAssistantEntryView(model: model)
                } label: {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Assistant")
                        Text("Ask questions about your timetable, tasks, grades, and campus resources.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            if feedbackEnabled {
                Section("Feedback") {
                    Button {
                        activeSheet = .appFeedback
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Send app feedback")
                            Text("Report an issue or suggest a feature without including university login details.")
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }

            Section {
                Toggle("Notify before lectures", isOn: reminderToggle)

                Picker("Reminder time", selection: reminderLeadTimeSelection) {
                    ForEach(AppModel.reminderLeadTimeOptions, id: \.self) { minutes in
                        Text("\(minutes) minutes before")
                            .tag(minutes)
                    }
                }
                .disabled(!model.remindersEnabled)

                if let message = model.reminderMessage {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            } header: {
                Text("Lecture reminders")
            } footer: {
                Text("Reminders are scheduled on this device from cached Alma timetable entries.")
            }
        }
        .navigationTitle("Settings")
        .task {
            await refreshFeedbackAvailability()
        }
        .sheet(item: $activeSheet) { sheet in
            switch sheet {
            case .appFeedback:
                AppFeedbackSheet(portalAPIBaseURLString: model.portalAPIBaseURLString)
            }
        }
    }

    private var reminderToggle: Binding<Bool> {
        Binding {
            model.remindersEnabled
        } set: { isEnabled in
            Task {
                if isEnabled {
                    await model.enableLectureReminders()
                } else {
                    await model.disableLectureReminders()
                }
            }
        }
    }

    private var reminderLeadTimeSelection: Binding<Int> {
        Binding {
            model.reminderLeadTimeMinutes
        } set: { minutes in
            Task {
                await model.setReminderLeadTime(minutes: minutes)
            }
        }
    }

    @MainActor
    private func refreshFeedbackAvailability() async {
        guard let client = BackendClient(baseURLString: model.portalAPIBaseURLString) else {
            feedbackEnabled = false
            return
        }

        do {
            feedbackEnabled = try await client.fetchAppFeedbackStatus().enabled
        } catch {
            feedbackEnabled = false
        }
    }
}

private enum SettingsSheet: String, Identifiable {
    case appFeedback

    var id: String { rawValue }
}
