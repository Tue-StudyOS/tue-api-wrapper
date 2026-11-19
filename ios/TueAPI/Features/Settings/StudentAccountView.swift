import SwiftUI
import WidgetKit

struct StudentAccountView: View {
    var model: AppModel
    var mailBadgeStore: MailBadgeStore

    var body: some View {
        List {
            StudentListHeading(title: "Account")
            if !model.hasCredentials {
                Section {
                    NavigationLink {
                        SettingsView(model: model)
                    } label: {
                        Label("Connect university account", systemImage: "person.badge.key")
                    }
                }
            }
            Section("University") {
                NavigationLink {
                    StudentDocumentsView(model: model)
                } label: {
                    Label("Documents", systemImage: "doc.text")
                }
                NavigationLink {
                    GradeOverviewView(model: model)
                } label: {
                    Label("Academic records", systemImage: "graduationcap")
                }
                NavigationLink {
                    MailView(model: model, mailBadgeStore: mailBadgeStore)
                } label: {
                    HStack {
                        Label("University mail", systemImage: "envelope")
                        Spacer()
                        if let summary = mailBadgeStore.unreadSummaryText {
                            Text(summary).foregroundStyle(.secondary)
                        }
                    }
                }
                NavigationLink {
                    TodayPortalMessagesCard(model: model)
                        .padding()
                        .navigationTitle("Alma notices")
        .navigationBarTitleDisplayMode(.inline)
                } label: {
                    Label("Alma notices", systemImage: "bell")
                }
            }
            Section("Device") {
                NavigationLink {
                    SettingsView(model: model)
                } label: {
                    Label("Connections and reminders", systemImage: "gearshape")
                }
                NavigationLink {
                    StudentWidgetGuide()
                } label: {
                    Label("Widgets", systemImage: "square.grid.2x2")
                }
            }
        }
        .navigationTitle("Account")
    }
}

private struct StudentWidgetGuide: View {
    @AppStorage(LectureWidgetPrivacy.detailsKey, store: UserDefaults(suiteName: AppGroup.identifier))
    private var showsLectureDetails = false
    var body: some View {
        List {
            StudentListHeading(title: "Widgets", detail: "Open the schedule, see KuF counts, or get to your saved pass.")
            Section("Lectures") {
                Text("Add Upcoming Lectures to the Home Screen or Lock Screen to see your next class.")
                Toggle("Show lecture details on Lock Screen", isOn: $showsLectureDetails)
                    .onChange(of: showsLectureDetails) {
                        WidgetCenter.shared.reloadTimelines(ofKind: "UpcomingLecturesWidget")
                        if !showsLectureDetails {
                            Task { await LiveActivityController.endAll() }
                        }
                    }
                Text("This also controls course titles and rooms in Live Activities.")
                Text("To start a Live Activity, open a lecture in Schedule.")
            }
            Section("KuF") {
                Text("Add KuF Pass to the Home Screen or Lock Screen. Tap it to open your saved barcode in the app.")
                Text("Add KuF Count to the Home Screen. Tap it to open training trends.")
            }
        }
        .navigationTitle("Widgets")
        .navigationBarTitleDisplayMode(.inline)
    }
}
