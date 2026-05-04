import SwiftUI

struct TodayView: View {
    var model: AppModel
    var mailBadgeStore: MailBadgeStore
    private let kufHistoryStore: KufOccupancyHistoryStore?

    @State private var kufOccupancy: KufTrainingOccupancy?
    @State private var kufError: String?
    @State private var isLoadingKuf = false

    private var nextLecture: LectureEvent? { model.events.first }

    private var urgencyItems: [TodayUrgencyItem] {
        let deadlines = model.deadlines.prefix(2).map {
            TodayUrgencyItem(
                title: $0.title,
                subtitle: $0.courseName ?? "Moodle deadline",
                detail: deadlineDetailText(for: $0),
                systemImage: "calendar.badge.clock",
                tint: .orange
            )
        }
        let tasks = model.tasks.prefix(max(0, 3 - deadlines.count)).map {
            TodayUrgencyItem(
                title: $0.title,
                subtitle: $0.itemType ?? "ILIAS task",
                detail: $0.end ?? "No deadline exposed",
                systemImage: "checklist",
                tint: .accentColor
            )
        }
        return Array(deadlines + tasks)
    }

    private var topStatusLine: TodayStatusLine? {
        if !model.hasCredentials {
            return TodayStatusLine(
                text: "Connect your university account in Settings to load Alma, Moodle, and ILIAS.",
                systemImage: "lock",
                tint: .secondary
            )
        }
        if model.phase == .loading || isLoadingKuf || (model.tasksPhase == .loading && urgencyItems.isEmpty) {
            return TodayStatusLine(
                text: "Refreshing your university data.",
                tint: .accentColor,
                isLoading: true
            )
        }
        if case .failed(let message) = model.phase {
            return TodayStatusLine(text: message, systemImage: "exclamationmark.triangle", tint: .orange)
        }
        if case .failed(let message) = model.tasksPhase {
            return TodayStatusLine(text: message, systemImage: "exclamationmark.triangle", tint: .orange)
        }
        return nil
    }

    private var footerTimestamp: String? {
        guard topStatusLine == nil, let refreshedAt = model.timetableRefreshedAt else {
            return nil
        }
        return "Last updated \(refreshedAt.formatted(date: .abbreviated, time: .shortened))"
    }

    init(
        model: AppModel,
        mailBadgeStore: MailBadgeStore,
        kufHistoryStore: KufOccupancyHistoryStore? = KufOccupancyHistoryStore()
    ) {
        self.model = model
        self.mailBadgeStore = mailBadgeStore
        self.kufHistoryStore = kufHistoryStore
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 18) {
                TodayIdentityHeader(
                    profileName: model.profileName,
                    termLabel: model.currentTermLabel,
                    hasCredentials: model.hasCredentials,
                    unreadMailText: mailBadgeStore.unreadSummaryText
                )

                if let topStatusLine {
                    AppInlineStatusLine(
                        text: topStatusLine.text,
                        systemImage: topStatusLine.systemImage,
                        tint: topStatusLine.tint,
                        isLoading: topStatusLine.isLoading
                    )
                }

                TodayNextLectureCard(
                    event: nextLecture,
                    isLoading: model.phase == .loading && nextLecture == nil,
                    hasCredentials: model.hasCredentials
                )

                TodayUrgencyCard(
                    items: urgencyItems,
                    isLoading: model.tasksPhase == .loading && urgencyItems.isEmpty,
                    hasCredentials: model.hasCredentials,
                    model: model
                )

                TodayPortalMessagesCard(model: model)

                TodayStudySnapshotCard(model: model)

                TodayCampusPulseCard(
                    occupancy: kufOccupancy,
                    errorMessage: kufError,
                    isLoading: isLoadingKuf
                )

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
                .disabled(model.phase == .loading || isLoadingKuf)
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
        if model.hasCredentials, model.phase == .idle, model.timetableRefreshedAt == nil {
            await model.refreshUpcomingLectures()
        }
        if model.tasksPhase == .idle {
            await model.refreshTasks()
        }
        if kufOccupancy == nil && kufError == nil {
            await refreshKuf()
        }
    }

    func refreshToday() async {
        await model.refreshUpcomingLectures()
        await model.refreshTasks()
        await mailBadgeStore.refreshIfNeeded(hasCredentials: model.hasCredentials, force: true)
        await refreshKuf()
    }

    func refreshKuf() async {
        isLoadingKuf = true
        defer { isLoadingKuf = false }

        guard let client = KufOccupancyClient() else {
            kufError = "Backend unavailable"
            return
        }

        do {
            let occupancy = try await client.fetchOccupancy()
            kufOccupancy = occupancy
            kufHistoryStore?.record(occupancy)
            kufError = nil
        } catch {
            kufError = error.localizedDescription
        }
    }

    func deadlineDetailText(for deadline: MoodleDeadline) -> String {
        if let formattedTime = deadline.formattedTime {
            let cleaned = HTMLText.stripTags(formattedTime)
            if !cleaned.isEmpty {
                return cleaned
            }
        }

        if let dueAt = deadline.dueAt {
            let cleaned = HTMLText.stripTags(dueAt)
            if !cleaned.isEmpty {
                return cleaned
            }
        }

        return "Due date unavailable"
    }
}

private struct TodayStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}
