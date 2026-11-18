import SwiftUI

struct CalendarTimelineView: View {
    var day: Date
    var events: [LectureEvent]
    var workItems: [TodayUrgencyItem] = []

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            AppSurfaceCard {
                VStack(alignment: .leading, spacing: 4) {
                    Text(CalendarSchedule.dayTitle(day))
                        .font(.title3.weight(.semibold))
                    Text(daySummary)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            if events.isEmpty && workItems.isEmpty {
                AppSurfaceCard {
                    ContentUnavailableView(
                        "No lectures this day",
                        systemImage: "calendar",
                        description: Text("Pick another day from the calendar strip.")
                    )
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 32)
                }
            } else {
                let firstScheduledID = events.first { !$0.isCancelled }?.id
                VStack(spacing: 12) {
                    ForEach(events) { event in
                        NavigationLink(value: event) {
                            CalendarAgendaCard(
                                event: event,
                                isFirst: event.id == firstScheduledID,
                                isHappeningNow: isHappeningNow(event)
                            )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

            if !workItems.isEmpty {
                AppSurfaceCard {
                    Text("Deadlines").font(.headline)
                    ForEach(workItems) { item in
                        NavigationLink {
                            TodayWorkDetail(item: item)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.title).font(.subheadline.weight(.semibold))
                                Text("\(item.detail) · \(item.source)").font(.footnote).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
    }

    private var daySummary: String {
        let cancellations = events.filter(\.isCancelled).count
        if cancellations > 0 {
            return "\(events.count - cancellations) scheduled · \(cancellations) canceled"
        }
        switch events.count {
        case 0:
            return "No lectures scheduled"
        case 1:
            return "1 lecture"
        default:
            return "\(events.count) lectures"
        }
    }

    private func isHappeningNow(_ event: LectureEvent) -> Bool {
        let now = Date()
        let end = event.endDate ?? event.startDate.addingTimeInterval(50 * 60)
        return !event.isCancelled && event.startDate <= now && now <= end
    }
}

private struct CalendarAgendaCard: View {
    let event: LectureEvent
    let isFirst: Bool
    let isHappeningNow: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Text(event.compactTimeRangeText)
                    .font(.subheadline.weight(.semibold))
                    .monospacedDigit()
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)
                if let relativeStartText {
                    Text(relativeStartText)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(event.calendarAccentColor)
                }
            }
            .frame(width: 92, alignment: .leading)

            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .top) {
                    Text(event.title)
                        .font(.headline)
                        .strikethrough(event.isCancelled)
                        .multilineTextAlignment(.leading)
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer(minLength: 8)
                    if isHappeningNow {
                        CalendarStatusBadge(text: "Now", tint: event.calendarAccentColor)
                    } else if isFirst {
                        CalendarStatusBadge(text: "Next", tint: event.calendarAccentColor)
                    }
                }

                if event.isCancelled {
                    CalendarMetadataRow(systemImage: "calendar.badge.minus", text: "Canceled")
                    if let reason = event.cancellationReason {
                        Text(reason)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }

                if let location = event.compactLocationText {
                    CalendarMetadataRow(systemImage: "mappin.and.ellipse", text: location)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.vertical, 16)
        .padding(.trailing, 16)
        .padding(.leading, 26)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(event.calendarAccentColor.opacity(0.08), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(alignment: .leading) {
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(event.calendarAccentColor)
                .frame(width: 6)
                .padding(.vertical, 14)
                .padding(.leading, 10)
        }
    }

    private var relativeStartText: String? {
        guard !event.isCancelled, !isHappeningNow, event.startDate > Date() else {
            return nil
        }
        return RelativeDateTimeFormatter().localizedString(for: event.startDate, relativeTo: Date())
    }
}

private struct CalendarMetadataRow: View {
    let systemImage: String
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: systemImage)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 14, alignment: .center)

            Text(text)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

private struct CalendarStatusBadge: View {
    let text: String
    let tint: Color

    var body: some View {
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundStyle(tint)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(tint.opacity(0.12), in: Capsule())
    }
}

private enum CalendarEventPalette {
    static let colors: [Color] = [
        .red,
        .orange,
        .blue,
        .teal,
        .green,
        .pink,
        .indigo,
        .brown
    ]

    static func color(for title: String) -> Color {
        let seed = title.unicodeScalars.reduce(0) { partial, scalar in
            partial + Int(scalar.value)
        }
        return colors[seed % colors.count]
    }
}

extension LectureEvent {
    var calendarAccentColor: Color {
        isCancelled ? .secondary : CalendarEventPalette.color(for: title)
    }

    var compactTimeRangeText: String {
        let formatter = DateFormatter()
        formatter.timeZone = CalendarSchedule.calendar.timeZone
        formatter.dateFormat = "HH:mm"

        guard let endDate else {
            return formatter.string(from: startDate)
        }
        return "\(formatter.string(from: startDate)) – \(formatter.string(from: endDate))"
    }

    var compactLocationText: String? {
        guard let location = location?.trimmedOrNil else {
            return nil
        }
        let normalizedLineBreaks = location.replacingOccurrences(of: "\n", with: ", ")
        let collapsedWhitespace = normalizedLineBreaks.replacingOccurrences(
            of: "\\s+",
            with: " ",
            options: .regularExpression
        )
        let normalizedCommas = collapsedWhitespace.replacingOccurrences(
            of: "\\s*,\\s*",
            with: ", ",
            options: .regularExpression
        )
        return normalizedCommas.trimmedOrNil
    }
}
