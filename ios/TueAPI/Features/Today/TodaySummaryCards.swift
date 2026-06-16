import SwiftUI

struct TodayUrgencyItem: Identifiable {
    let id = UUID()
    let title: String
    let subtitle: String
    let detail: String
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
                Text("Urgent")
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
                    "Nothing urgent",
                    systemImage: "checkmark.circle",
                    description: Text(
                        hasCredentials
                            ? "No actionable Moodle deadlines, ILIAS submissions, or ILIAS tasks are visible."
                            : "Connect university services to load deadlines and tasks."
                    )
                )
            } else {
                VStack(spacing: 14) {
                    ForEach(items) { item in
                        TodayUrgencyRow(item: item)
                    }
                }
            }
        }
    }
}

struct TodayStudySnapshotCard: View {
    let model: AppModel

    var body: some View {
        AppSurfaceCard {
            HStack(alignment: .firstTextBaseline) {
                Text("Study Snapshot")
                    .font(.title3.weight(.semibold))
                Spacer()
                if let termLabel = model.currentTermLabel {
                    Text(termLabel)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            if let summary = model.semesterCredits {
                VStack(alignment: .leading, spacing: 14) {
                    HStack(alignment: .lastTextBaseline) {
                        Text(summary.creditsText)
                            .font(.system(.largeTitle, design: .rounded, weight: .bold))
                        Text("ECTS saved")
                            .font(.headline)
                            .foregroundStyle(.secondary)
                        Spacer()
                        if let coverageBadge = summary.coverageBadgeText {
                            Text(coverageBadge)
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(Color.accentColor)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 7)
                                .background(Color.accentColor.opacity(0.08), in: Capsule())
                        }
                    }

                    Text(summary.coverageDescription)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text("Refresh Alma to load credits for the current term.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 12) {
                NavigationLink {
                    GradeOverviewView(model: model)
                } label: {
                    TodayQuickActionLabel(title: "Grades", systemImage: "chart.bar")
                }

                NavigationLink {
                    CoursesView(model: model)
                } label: {
                    TodayQuickActionLabel(title: "Courses", systemImage: "magnifyingglass")
                }
            }
        }
    }
}

struct TodayCampusPulseCard: View {
    let occupancy: KufTrainingOccupancy?
    let errorMessage: String?
    let isLoading: Bool

    var body: some View {
        AppSurfaceCard {
            Text("Campus Pulse")
                .font(.title3.weight(.semibold))

            TodayPulseMetric(
                title: "KuF right now",
                value: occupancyValue,
                caption: occupancyCaption,
                systemImage: "figure.run",
                tint: .accentColor
            )

            HStack(spacing: 12) {
                NavigationLink {
                    CampusMapView()
                } label: {
                    TodayQuickActionLabel(title: "Campus map", systemImage: "map")
                }

                NavigationLink {
                    KufOccupancyHistoryView()
                } label: {
                    TodayQuickActionLabel(title: "KuF trends", systemImage: "chart.bar.xaxis")
                }
            }
        }
    }

    private var occupancyValue: String {
        if isLoading { return "..." }
        if let occupancy { return "\(occupancy.count)" }
        return "—"
    }

    private var occupancyCaption: String {
        if occupancy != nil { return "Current headcount" }
        return errorMessage ?? "Unavailable"
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
                Text(item.detail)
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(item.tint)
            }

            Spacer(minLength: 0)
        }
    }
}

private struct TodayPulseMetric: View {
    let title: String
    let value: String
    let caption: String
    let systemImage: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label(title, systemImage: systemImage)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(tint)
            Text(value)
                .font(.system(.title2, design: .rounded, weight: .bold))
            Text(caption)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(tint.opacity(0.08), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

private struct TodayQuickActionLabel: View {
    let title: String
    let systemImage: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
            Text(title)
                .lineLimit(1)
                .minimumScaleFactor(0.9)
        }
        .font(.subheadline.weight(.semibold))
        .frame(maxWidth: .infinity, minHeight: 44)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.accentColor.opacity(0.08), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

private extension SemesterCreditSummary {
    var coverageBadgeText: String? {
        guard unresolvedCourseCount > 0 else { return nil }
        return unresolvedCourseCount == 1 ? "1 entry missing CP" : "\(unresolvedCourseCount) entries missing CP"
    }

    var coverageDescription: String {
        if unresolvedCourseCount > 0 {
            return unresolvedCourseCount == 1
                ? "One visible timetable entry still has no CP value from Alma."
                : "\(unresolvedCourseCount) visible timetable entries still have no CP value from Alma."
        }
        return "All visible timetable entries currently expose CP values in Alma."
    }

    var creditsText: String {
        totalCredits.rounded() == totalCredits
            ? "\(Int(totalCredits))"
            : String(format: "%.1f", totalCredits)
    }
}
