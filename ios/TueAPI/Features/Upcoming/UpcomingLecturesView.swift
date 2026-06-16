import SwiftUI
import UIKit

struct UpcomingLecturesView: View {
    var model: AppModel

    var body: some View {
        List {
            Section {
                statusContent
            }

            if let event = model.events.first {
                Section("Live Activity") {
                    Button("Start for next lecture") {
                        model.startLiveActivity(for: event)
                    }
                    Button("End live activities", role: .destructive) {
                        Task { await model.endLiveActivities() }
                    }
                    if let message = model.liveActivityMessage {
                        Text(message)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            lecturesSection

            deadlinesSection
        }
        .navigationTitle("Schedule")
        .navigationDestination(for: LectureEvent.self) { event in
            CourseDetailView(event: event, model: model)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task {
                        await model.refreshUpcomingLectures()
                        await model.refreshTasks()
                    }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(model.phase == .loading)
            }
        }
        .refreshable {
            await model.refreshUpcomingLectures()
            await model.refreshTasks()
        }
        .task {
            await model.refreshTasks()
        }
    }

    // MARK: - Lectures Section

    @ViewBuilder
    private var lecturesSection: some View {
        Section("Next lectures") {
            if model.events.isEmpty {
                if model.phase == .loading {
                    // Skeleton rows on first load
                    ForEach(0..<4, id: \.self) { _ in
                        LectureEventRow(event: .placeholder)
                    }
                    .redacted(reason: .placeholder)
                } else {
                    ContentUnavailableView(
                        "No cached lectures",
                        systemImage: "calendar.badge.exclamationmark",
                        description: Text("Connect your university account, then refresh Alma to cache upcoming timetable entries.")
                    )
                }
            } else {
                ForEach(model.events) { event in
                    NavigationLink(value: event) {
                        LectureEventRow(event: event)
                    }
                    // Swipe left → copy room to clipboard
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        if let location = event.location, !location.isEmpty {
                            Button {
                                UIPasteboard.general.string = location
                            } label: {
                                Label("Copy Room", systemImage: "doc.on.doc")
                            }
                            .tint(.blue)
                        }
                    }
                    // Swipe right → start Live Activity for this lecture
                    .swipeActions(edge: .leading, allowsFullSwipe: false) {
                        Button {
                            model.startLiveActivity(for: event)
                        } label: {
                            Label("Live Activity", systemImage: "livephoto")
                        }
                        .tint(.purple)
                    }
                }
            }
        }
    }

    // MARK: - Deadlines Section

    @ViewBuilder
    private var deadlinesSection: some View {
        switch model.tasksPhase {
        case .idle, .unavailable:
            EmptyView()

        case .loading:
            Section("Deadlines") {
                ForEach(0..<3, id: \.self) { _ in
                    DeadlineSkeletonRow()
                }
                .redacted(reason: .placeholder)
            }

        case .failed(let message):
            Section("Deadlines") {
                StatusBanner(title: "Deadlines unavailable", message: message, systemImage: "exclamationmark.triangle")
            }

        case .loaded:
            let allItems = model.deadlines.count + model.iliasAssignments.count + model.tasks.count
            if allItems > 0 {
                Section("Upcoming Deadlines") {
                    ForEach(model.deadlines) { deadline in
                        StudyDeadlineRow(deadline: deadline)
                    }
                    ForEach(model.iliasAssignments) { deadline in
                        StudyIliasAssignmentRow(deadline: deadline)
                    }
                    ForEach(model.tasks) { task in
                        StudyIliasTaskRow(task: task)
                    }
                }
            } else if let warning = model.tasksWarning {
                Section("Deadlines") {
                    StatusBanner(title: "Study systems unavailable", message: warning, systemImage: "exclamationmark.triangle")
                }
            }
        }
    }

    // MARK: - Status Banner

    @ViewBuilder
    private var statusContent: some View {
        switch model.phase {
        case .idle:
            StatusBanner(
                title: model.hasCredentials ? "Ready for Alma" : "Login required",
                message: model.hasCredentials
                    ? statusMessage("Refresh to fetch the current Alma timetable directly.")
                    : "Connect your university account before refreshing.",
                systemImage: model.hasCredentials ? "checkmark.seal" : "key"
            )
        case .loading:
            ProgressView("Refreshing Alma timetable")
        case .loaded(let date, let term):
            StatusBanner(
                title: "Updated",
                message: statusMessage(
                    "\(term) refreshed \(date.formatted(date: .abbreviated, time: .shortened)). Widgets were reloaded."
                ),
                systemImage: "calendar.badge.clock"
            )
        case .failed(let message):
            StatusBanner(title: "Refresh failed", message: message, systemImage: "exclamationmark.triangle")
        }
    }

    private func statusMessage(_ base: String) -> String {
        guard let semesterCredits = model.semesterCredits else {
            return base
        }
        return "\(base) \(semesterCredits.displayText)."
    }
}

// MARK: - Lecture Row

struct LectureEventRow: View {
    var event: LectureEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(event.title)
                .font(.headline)
            Text(event.timeRangeText)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if let location = event.location, !location.isEmpty {
                Label(location, systemImage: "mappin.and.ellipse")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Skeleton placeholder for deadlines

private struct DeadlineSkeletonRow: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Introduction to Scientific Writing — Week 4 Essay")
                .font(.subheadline.weight(.medium))
                .lineLimit(2)
            Text("Machine Learning · Due Mon 14 Apr 23:59")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 2)
    }
}
