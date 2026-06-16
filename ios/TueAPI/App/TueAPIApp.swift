import BackgroundTasks
import SwiftUI

@main
struct TueAPIApp: App {
    @State private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            AppRootView(model: model)
        }
        .backgroundTask(.appRefresh(StudyBackgroundRefreshService.taskIdentifier)) {
            await StudyBackgroundRefreshService.handleAppRefresh()
        }
    }
}
