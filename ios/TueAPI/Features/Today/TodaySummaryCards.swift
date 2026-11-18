import SwiftUI

struct TodayUrgencyItem: Identifiable {
    let id: String
    let dueDate: Date?
    let title: String
    let subtitle: String
    let detail: String
    let source: String
    let sourceURL: URL?
    var status: String? = nil
    var lastSubmission: String? = nil
    var requirement: String? = nil
    let systemImage: String
    let tint: Color
}

struct TodayUrgencyCard: View {
    let items: [TodayUrgencyItem]
    let isLoading: Bool
    let hasCredentials: Bool
    let model: AppModel

    var body: some View {
        AppSurfaceCard {
            HStack(alignment: .firstTextBaseline) {
                Text("Due and to do")
                    .font(.title3.weight(.semibold))
                Spacer()
                NavigationLink("Open all") {
                    StudyTasksView(model: model)
                }
                .font(.subheadline.weight(.semibold))
            }

            if isLoading {
                VStack(spacing: 12) {
                    StudyDeadlineSkeletonRow()
                    StudyIliasAssignmentSkeletonRow()
                    StudyDeadlineSkeletonRow()
                }
            } else if items.isEmpty {
                ContentUnavailableView(
                    "No tasks shown",
                    systemImage: "checkmark.circle",
                    description: Text(
                        hasCredentials
                            ? "No actionable Moodle deadlines, ILIAS submissions, or ILIAS tasks are visible."
                            : "Connect university services to load deadlines and tasks."
                    )
                )
            } else {
                let dated = items.filter { $0.dueDate != nil }
                let undated = items.filter { $0.dueDate == nil }
                workRows(dated)
                if !undated.isEmpty {
                    Text("No confirmed due date")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.secondary)
                    workRows(undated)
                }
            }
        }
    }
    private func workRows(_ rows: [TodayUrgencyItem]) -> some View {
        ForEach(rows) { item in
            NavigationLink {
                TodayWorkDetail(item: item)
            } label: {
                TodayUrgencyRow(item: item)
            }
            .buttonStyle(.plain)
        }
    }
}

private struct TodayUrgencyRow: View {
    let item: TodayUrgencyItem

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: item.systemImage)
                .font(.headline)
                .foregroundStyle(item.tint)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 4) {
                Text(item.title)
                    .font(.headline)
                    .lineLimit(2)
                Text(item.subtitle)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text("\(item.detail) · \(item.source)")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(item.tint)
            }

            Spacer(minLength: 0)
        }
    }
}
