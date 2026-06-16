import SwiftUI

struct StudyTasksView: View {
    var model: AppModel

    private var isRefreshing: Bool {
        model.tasksPhase == .loading || (
            model.tasksPhase == .idle &&
            model.deadlines.isEmpty &&
            model.iliasAssignments.isEmpty &&
            model.tasks.isEmpty
        )
    }

    private var topStatusLine: StudyTasksStatusLine? {
        if isRefreshing {
            return StudyTasksStatusLine(
                text: "Refreshing Moodle deadlines, ILIAS submissions, and ILIAS tasks.",
                tint: .accentColor,
                isLoading: true
            )
        }
        switch model.tasksPhase {
        case .unavailable:
            return StudyTasksStatusLine(
                text: "Connect your university account to load study tasks.",
                systemImage: "lock",
                tint: .secondary
            )
        case .loaded where model.tasksWarning != nil:
            return StudyTasksStatusLine(
                text: model.tasksWarning ?? "",
                systemImage: "exclamationmark.triangle",
                tint: .orange
            )
        case .failed(let message):
            return StudyTasksStatusLine(
                text: message,
                systemImage: "exclamationmark.triangle",
                tint: .orange
            )
        default:
            return nil
        }
    }

    private var footerTimestamp: String? {
        guard case .loaded(let date) = model.tasksPhase else { return nil }
        return "Last updated \(date.formatted(date: .abbreviated, time: .shortened))"
    }

    private var primaryEmptyState: StudyEmptyState? {
        guard model.deadlines.isEmpty, model.iliasAssignments.isEmpty, model.tasks.isEmpty else { return nil }
        guard !isRefreshing else { return nil }
        switch model.tasksPhase {
        case .unavailable:
            return StudyEmptyState(
                title: "Login required",
                systemImage: "key",
                message: "Connect your university account to load ILIAS tasks and Moodle deadlines."
            )
        case .loaded where model.tasksWarning != nil:
            return StudyEmptyState(
                title: "Study systems unavailable",
                systemImage: "exclamationmark.triangle",
                message: model.tasksWarning ?? "Refresh to try loading your study data again."
            )
        case .failed:
            return StudyEmptyState(
                title: "Tasks unavailable",
                systemImage: "exclamationmark.triangle",
                message: "Refresh to try loading your study data again."
            )
        default:
            return nil
        }
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                if let topStatusLine {
                    AppInlineStatusLine(
                        text: topStatusLine.text,
                        systemImage: topStatusLine.systemImage,
                        tint: topStatusLine.tint,
                        isLoading: topStatusLine.isLoading
                    )
                }

                if let primaryEmptyState {
                    AppSurfaceCard {
                        ContentUnavailableView(
                            primaryEmptyState.title,
                            systemImage: primaryEmptyState.systemImage,
                            description: Text(primaryEmptyState.message)
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 28)
                    }
                } else {
                    deadlinesCard
                    iliasAssignmentsCard
                    iliasTasksCard
                }

                if let footerTimestamp {
                    Text(footerTimestamp)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)
                }
            }
            .padding(16)
            .padding(.bottom, 124)
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("Tasks")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await model.refreshTasks() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(isRefreshing)
            }
        }
        .task {
            if model.tasksPhase == .idle {
                await model.refreshTasks()
            }
        }
        .refreshable {
            await model.refreshTasks()
        }
    }

    private var deadlinesCard: some View {
        AppSurfaceCard {
            sectionHeader("Deadlines", systemImage: "calendar.badge.clock", count: model.deadlines.count)

            if isRefreshing && model.deadlines.isEmpty {
                VStack(spacing: 14) {
                    ForEach(0..<3, id: \.self) { _ in
                        StudyDeadlineSkeletonRow()
                    }
                }
            } else if model.deadlines.isEmpty {
                ContentUnavailableView(
                    "No deadlines",
                    systemImage: "calendar.badge.checkmark",
                    description: Text("No actionable Moodle deadlines are visible right now.")
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
            } else {
                VStack(spacing: 14) {
                    ForEach(Array(model.deadlines.enumerated()), id: \.element.id) { index, deadline in
                        StudyDeadlineRow(deadline: deadline)
                        if index < model.deadlines.count - 1 {
                            Divider()
                        }
                    }
                }
            }
        }
    }

    private var iliasTasksCard: some View {
        AppSurfaceCard {
            sectionHeader("ILIAS tasks", systemImage: "checklist", count: model.tasks.count)

            if isRefreshing && model.tasks.isEmpty {
                VStack(spacing: 14) {
                    ForEach(0..<3, id: \.self) { _ in
                        StudyIliasTaskSkeletonRow()
                    }
                }
            } else if model.tasks.isEmpty {
                ContentUnavailableView(
                    "No ILIAS tasks",
                    systemImage: "checklist",
                    description: Text("No current task rows are visible in ILIAS.")
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
            } else {
                VStack(spacing: 14) {
                    ForEach(Array(model.tasks.enumerated()), id: \.element.id) { index, task in
                        StudyIliasTaskRow(task: task)
                        if index < model.tasks.count - 1 {
                            Divider()
                        }
                    }
                }
            }
        }
    }

    private var iliasAssignmentsCard: some View {
        AppSurfaceCard {
            sectionHeader("ILIAS submissions", systemImage: "tray.and.arrow.up", count: model.iliasAssignments.count)

            if isRefreshing && model.iliasAssignments.isEmpty {
                VStack(spacing: 14) {
                    ForEach(0..<3, id: \.self) { _ in
                        StudyIliasAssignmentSkeletonRow()
                    }
                }
            } else if model.iliasAssignments.isEmpty {
                ContentUnavailableView(
                    "No ILIAS submissions",
                    systemImage: "tray.and.arrow.up",
                    description: Text("No visible exercise submissions were found in your joined ILIAS courses.")
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
            } else {
                VStack(spacing: 14) {
                    ForEach(Array(model.iliasAssignments.enumerated()), id: \.element.id) { index, deadline in
                        StudyIliasAssignmentRow(deadline: deadline)
                        if index < model.iliasAssignments.count - 1 {
                            Divider()
                        }
                    }
                }
            }
        }
    }

    private func sectionHeader(_ title: String, systemImage: String, count: Int) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Label(title, systemImage: systemImage)
                .font(.headline)

            Spacer()

            if count > 0 {
                Text("\(count)")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color(uiColor: .secondarySystemBackground), in: Capsule())
            }
        }
    }
}

private struct StudyTasksStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}

private struct StudyEmptyState {
    let title: String
    let systemImage: String
    let message: String
}
