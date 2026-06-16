import Foundation

extension AppModel {
    func refreshTasks() async {
        tasksPhase = .loading

        do {
            let snapshot = try await UniversityPortalClient(credentialsLoader: keychain)
                .fetchTasksAndDeadlines()
            tasks = snapshot.tasks
            iliasAssignments = snapshot.iliasAssignments
            deadlines = snapshot.deadlines.filter { $0.isActionable }
            tasksWarning = snapshot.warningMessage
            tasksPhase = .loaded(snapshot.refreshedAt)
        } catch UniversityPortalError.missingCredentials {
            tasks = []
            iliasAssignments = []
            deadlines = []
            tasksWarning = nil
            tasksPhase = .unavailable
        } catch {
            tasksWarning = nil
            tasksPhase = .failed(error.localizedDescription)
        }
    }
}
