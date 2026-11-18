import SwiftUI

struct AppView: View {
    var model: AppModel
    @Environment(\.scenePhase) private var scenePhase
    @State private var mailBadgeStore = MailBadgeStore()
    @State private var selectedTab: StudentTab

    init(model: AppModel) {
        self.model = model
        _selectedTab = State(initialValue: model.hasCredentials ? .today : .campus)
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationStack {
                TodayView(model: model, mailBadgeStore: mailBadgeStore)
                    .accountToolbar(model: model, mailBadgeStore: mailBadgeStore)
            }
            .tag(StudentTab.today)
            .tabItem {
                Label("Today", systemImage: "sun.max")
            }

            NavigationStack {
                CalendarScheduleView(model: model)
                    .accountToolbar(model: model, mailBadgeStore: mailBadgeStore)
            }
            .tag(StudentTab.schedule)
            .tabItem {
                Label("Schedule", systemImage: "calendar.day.timeline.left")
            }

            NavigationStack {
                CoursesView(model: model)
                    .accountToolbar(model: model, mailBadgeStore: mailBadgeStore)
            }
            .tag(StudentTab.courses)
            .tabItem {
                Label("Courses", systemImage: "graduationcap")
            }

            NavigationStack {
                DiscoverView(model: model)
                    .accountToolbar(model: model, mailBadgeStore: mailBadgeStore)
            }
            .tag(StudentTab.campus)
            .tabItem {
                Label("Campus", systemImage: "map")
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

private enum StudentTab: Hashable {
    case today, schedule, courses, campus
}
