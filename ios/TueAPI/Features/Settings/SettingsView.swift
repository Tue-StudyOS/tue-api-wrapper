import SwiftUI

struct SettingsView: View {
    @Bindable var model: AppModel
    @State private var username = ""
    @State private var password = ""
    @State private var showsDisconnectConfirmation = false

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
                    let previous = model.credentialRevision
                    model.saveCredentials(username: username, password: password)
                    if model.phase == .idle || model.credentialRevision != previous {
                        password = ""
                        Task {
                            async let alma: Void = model.refreshUpcomingLectures()
                            async let tasks: Void = model.refreshTasks()
                            _ = await (alma, tasks)
                        }
                    }
                }
                .disabled(username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || password.isEmpty)

                if model.hasCredentials {
                    Button("Disconnect account", role: .destructive) {
                        showsDisconnectConfirmation = true
                    }
                }
            }

            Section("Source status") {
                if model.hasCredentials {
                    LabeledContent("University login", value: "Saved on this device")
                    if model.phase == .loading {
                        ProgressView("Checking Alma")
                    } else if case .loaded(let date, _) = model.phase {
                        LabeledContent("Alma timetable", value: date.formatted(date: .abbreviated, time: .shortened))
                    } else if case .failed(let message) = model.phase {
                        Text(message).foregroundStyle(.secondary)
                    }
                    if let warning = model.tasksWarning {
                        Text(warning).foregroundStyle(.secondary)
                    } else if case .loaded(let date) = model.tasksPhase {
                        LabeledContent("Moodle and ILIAS", value: date.formatted(date: .abbreviated, time: .shortened))
                    } else if case .failed(let message) = model.tasksPhase {
                        Text(message).foregroundStyle(.secondary)
                    }
                } else {
                    Text("Connect your account to check your timetable, work and university mail.")
                    if case .failed(let message) = model.phase {
                        Text(message).foregroundStyle(.secondary)
                    }
                }
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

            Section {
                Toggle("Notify near submission deadlines", isOn: submissionReminderToggle)

                if let message = model.submissionReminderMessage {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            } header: {
                Text("Submission reminders")
            } footer: {
                Text("Reminds once when an open ILIAS submission has no recorded upload and is due within three days.")
            }
        }
        .navigationTitle("Connections and reminders")
        .confirmationDialog("Disconnect university account?", isPresented: $showsDisconnectConfirmation, titleVisibility: .visible) {
            Button("Disconnect", role: .destructive) {
                model.deleteCredentials()
                password = ""
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This removes your saved login, timetable and deadlines from this device.")
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

    private var submissionReminderToggle: Binding<Bool> {
        Binding {
            model.submissionRemindersEnabled
        } set: { isEnabled in
            Task {
                if isEnabled {
                    await model.enableSubmissionReminders()
                } else {
                    await model.disableSubmissionReminders()
                }
            }
        }
    }
}
