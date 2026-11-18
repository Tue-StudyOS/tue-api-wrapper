import SwiftUI

struct TodayView: View {
    var model: AppModel
    var mailBadgeStore: MailBadgeStore

    private var nextLecture: LectureEvent? { model.scheduledLectures.first }

    private var urgencyItems: [TodayUrgencyItem] {
        let items = model.studyWorkItems
        return Array(items.filter { $0.dueDate != nil }.prefix(3))
            + Array(items.filter { $0.dueDate == nil }.prefix(1))
    }

    private var statusLines: [TodayStatusLine] {
        if !model.hasCredentials {
            return [TodayStatusLine(
                text: "Connect your university account in Account to check Alma, Moodle and ILIAS.",
                systemImage: "lock",
                tint: .secondary
            )]
        }
        var lines: [TodayStatusLine] = []
        if model.phase == .loading || (model.tasksPhase == .loading && urgencyItems.isEmpty) {
            lines.append(TodayStatusLine(text: "Refreshing university data.", tint: .accentColor, isLoading: true))
        }
        if case .failed(let message) = model.phase {
            lines.append(TodayStatusLine(text: "Alma timetable: \(message)", systemImage: "exclamationmark.triangle", tint: .orange))
        }
        if case .loaded = model.tasksPhase, let warning = model.tasksWarning {
            lines.append(TodayStatusLine(text: warning, systemImage: "exclamationmark.triangle", tint: .orange))
        }
        if case .failed(let message) = model.tasksPhase {
            lines.append(TodayStatusLine(text: "Deadlines: \(message)", systemImage: "exclamationmark.triangle", tint: .orange))
        }
        return lines
    }

    private var footerTimestamp: String? {
        guard let refreshedAt = model.timetableRefreshedAt else { return nil }
        return "Alma timetable checked \(refreshedAt.formatted(date: .abbreviated, time: .shortened))"
    }

    init(
        model: AppModel,
        mailBadgeStore: MailBadgeStore
    ) {
        self.model = model
        self.mailBadgeStore = mailBadgeStore
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 18) {
                TodayIdentityHeader(
                    termLabel: model.currentTermLabel,
                    unreadMailText: mailBadgeStore.unreadSummaryText
                )

                ForEach(statusLines, id: \.text) { status in
                    AppInlineStatusLine(
                        text: status.text,
                        systemImage: status.systemImage,
                        tint: status.tint,
                        isLoading: status.isLoading
                    )
                }

                TodayNextLectureCard(
                    event: nextLecture,
                    isLoading: model.phase == .loading && nextLecture == nil,
                    hasCredentials: model.hasCredentials
                )

                TodayCancellationsCard(events: model.events.filter(\.isCancelled), model: model)

                TodayUrgencyCard(
                    items: urgencyItems,
                    isLoading: model.tasksPhase == .loading && urgencyItems.isEmpty,
                    hasCredentials: model.hasCredentials,
                    model: model
                )

                TodayDocumentsLink(model: model)

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
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(for: LectureEvent.self) { event in
            CourseDetailView(event: event, model: model)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: refreshButtonTapped) {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(model.phase == .loading)
            }
        }
        .task {
            await loadAmbientDataIfNeeded()
        }
        .refreshable {
            await refreshToday()
        }
    }
}

private extension TodayView {
    func refreshButtonTapped() {
        Task { await refreshToday() }
    }

    func loadAmbientDataIfNeeded() async {
        if model.phase != .loading, model.shouldRefreshUpcomingLectures() {
            await model.refreshUpcomingLectures()
        }
        if model.shouldRefreshTasks() {
            await model.refreshTasks()
        }
    }

    func refreshToday() async {
        await model.refreshUpcomingLectures()
        await model.refreshTasks()
        await mailBadgeStore.refreshIfNeeded(hasCredentials: model.hasCredentials, force: true)
    }


}

private struct TodayStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}
