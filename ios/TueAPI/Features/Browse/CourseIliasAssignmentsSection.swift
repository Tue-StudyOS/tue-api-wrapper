import SwiftUI

struct CourseIliasAssignmentsSection: View {
    var target: URL
    var credentialsLoader: UniversityCredentialsLoading

    @State private var phase: CourseIliasAssignmentsPhase = .idle

    var body: some View {
        Section("ILIAS assignments") {
            content
        }
        .task(id: target.absoluteString) {
            await load()
        }
    }

    @ViewBuilder
    private var content: some View {
        switch phase {
        case .idle, .loading:
            ProgressView("Loading ILIAS assignments")
        case .unavailable(let message):
            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        case .failed(let message):
            StatusBanner(title: "ILIAS assignments unavailable", message: message, systemImage: "exclamationmark.triangle")
        case .loaded(let page):
            if page.exercises.isEmpty {
                Text("No exercise assignment lists were found in this ILIAS space.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(page.exercises) { group in
                    CourseIliasExerciseAssignmentsRow(group: group)
                }
            }
        }
    }

    private func load() async {
        phase = .loading
        do {
            guard let credentials = try credentialsLoader.load() else {
                phase = .unavailable("Connect your university account in Settings to load ILIAS assignments.")
                return
            }
            let page = try await IliasOnDeviceClient(credentials: credentials)
                .fetchCourseAssignments(target: target.absoluteString)
            phase = .loaded(page)
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

private struct CourseIliasExerciseAssignmentsRow: View {
    var group: IliasCourseExerciseAssignments

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label(group.exercise.label, systemImage: "tray.full")
                .font(.subheadline.weight(.semibold))

            if group.assignments.isEmpty {
                Text("No visible assignments in this exercise.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(group.assignments) { assignment in
                    CourseIliasAssignmentRow(assignment: assignment)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

private struct CourseIliasAssignmentRow: View {
    var assignment: IliasExerciseAssignment

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(assignment.title)
                .font(.subheadline)
            HStack(spacing: 8) {
                if let due = assignment.dueAt ?? assignment.dueHint {
                    Label(due, systemImage: "clock")
                        .foregroundStyle(.orange)
                }
                if let status = assignment.status {
                    Label(status, systemImage: "checklist")
                }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
            if let url = URL(string: assignment.url) {
                Link("Open assignment", destination: url)
                    .font(.caption.weight(.semibold))
            }
        }
    }
}

private enum CourseIliasAssignmentsPhase {
    case idle
    case loading
    case loaded(IliasCourseAssignmentsPage)
    case unavailable(String)
    case failed(String)
}
