import SwiftUI

struct TodayIdentityHeader: View {
    let termLabel: String?
    let unreadMailText: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            StudentScreenHeading(
                title: "Today",
                detail: Date.now.formatted(.dateTime.weekday(.wide).day().month(.wide))
            )
            if let termLabel, !termLabel.isEmpty {
                Text(termLabel)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            if let unreadMailText {
                Label(unreadMailText, systemImage: "envelope")
                    .font(.footnote.weight(.medium))
                    .foregroundStyle(.secondary)
            }
        }
    }
}

struct TodayNextLectureCard: View {
    let event: LectureEvent?
    let isLoading: Bool
    let hasCredentials: Bool

    var body: some View {
        Group {
            if let event {
                NavigationLink(value: event) {
                    lectureCard(for: event)
                }
                .buttonStyle(.plain)
            } else {
                emptyCard
            }
        }
    }

    private func lectureCard(for event: LectureEvent) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Next · \(dayTimeText(for: event))")
                .font(.subheadline.weight(.semibold))
            Text(event.title)
                .font(.title3.bold())
            if let location = event.location, !location.isEmpty {
                Label(location, systemImage: "mappin.and.ellipse")
                    .font(.subheadline)
            }
        }
        .foregroundStyle(.white)
        .multilineTextAlignment(.leading)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(Color.studentActionFill, in: RoundedRectangle(cornerRadius: 18))
    }

    private var emptyCard: some View {
        AppSurfaceCard {
            Text("Next Lecture")
                .font(.caption.weight(.semibold))
                .foregroundStyle(Color.accentColor)
                .textCase(.uppercase)

            if isLoading {
                AppInlineStatusLine(
                    text: "Looking up your next class.",
                    tint: .accentColor,
                    isLoading: true
                )
            } else {
                ContentUnavailableView(
                    "No upcoming lecture",
                    systemImage: "calendar.badge.exclamationmark",
                    description: Text(
                        hasCredentials
                            ? "Refresh Alma to load your upcoming timetable."
                            : "Connect your university account in Settings, then refresh Alma."
                    )
                )
            }
        }
    }

    private func dayTimeText(for event: LectureEvent) -> String {
        if Calendar.current.isDateInToday(event.startDate) {
            return event.timeRangeText
        }
        return event.startDate.formatted(.dateTime.weekday(.wide).hour().minute())
    }

}
