import SwiftUI

struct AppView: View {
    var model: AppModel
    @Environment(\.scenePhase) private var scenePhase
    @State private var mailBadgeStore = MailBadgeStore()

    var body: some View {
        TabView {
            NavigationStack {
                TodayView(model: model, mailBadgeStore: mailBadgeStore)
                    .settingsToolbar(model: model)
            }
            .tabItem {
                Label("Today", systemImage: "sun.max")
            }

            NavigationStack {
                CalendarScheduleView(model: model)
                    .settingsToolbar(model: model)
            }
            .tabItem {
                Label("Schedule", systemImage: "calendar.day.timeline.left")
            }

            NavigationStack {
                StudyView(model: model)
                    .settingsToolbar(model: model)
            }
            .tabItem {
                Label("Study", systemImage: "graduationcap")
            }

            NavigationStack {
                MailView(model: model, mailBadgeStore: mailBadgeStore)
                    .settingsToolbar(model: model)
            }
            .tabItem {
                Label("Inbox", systemImage: "envelope")
            }
            .badge(mailBadgeStore.tabBadgeCount)

            NavigationStack {
                DiscoverView(model: model)
                    .settingsToolbar(model: model)
            }
            .tabItem {
                Label("Discover", systemImage: "sparkle.magnifyingglass")
            }
        }
        .task {
            StudyBackgroundRefreshService.schedule()
            await model.refreshReminderStatus()
            await model.refreshSubmissionReminderStatus()
            await mailBadgeStore.refreshIfNeeded(hasCredentials: model.hasCredentials, force: true)
        }
        .onChange(of: scenePhase) {
            if scenePhase == .background {
                StudyBackgroundRefreshService.schedule()
                return
            }
            guard scenePhase == .active else {
                return
            }
            Task {
                if model.shouldRefreshUpcomingLectures() {
                    await model.refreshUpcomingLectures()
                }
                if model.shouldRefreshTasks() {
                    await model.refreshTasks()
                }
                await mailBadgeStore.refreshIfNeeded(hasCredentials: model.hasCredentials)
            }
        }
        .onChange(of: model.hasCredentials) {
            Task {
                await model.refreshSubmissionReminderStatus()
                await mailBadgeStore.refreshIfNeeded(hasCredentials: model.hasCredentials, force: true)
            }
        }
    }
}
