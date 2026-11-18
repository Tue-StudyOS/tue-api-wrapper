import SwiftUI

struct CalendarHeader: View {
    let subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Calendar")
                .font(.largeTitle.weight(.bold))
            Text(subtitle)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }
}

struct CalendarDayStrip: View {
    var days: [Date]
    var selectedDay: Date
    var eventsForDay: (Date) -> [LectureEvent]
    var selectDay: (Date) -> Void

    private var contextualDays: [Date] {
        CalendarSchedule.contextualDays(from: days)
    }

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(contextualDays, id: \.self) { day in
                    let dayEvents = eventsForDay(day)
                    Button {
                        selectDay(day)
                    } label: {
                        CalendarDayChip(
                            day: day,
                            isSelected: CalendarSchedule.isSameDay(day, selectedDay),
                            isEnabled: !dayEvents.isEmpty,
                            eventCount: dayEvents.count,
                            previewColors: Array(dayEvents.prefix(3).map(\.calendarAccentColor))
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 2)
        }
    }
}

struct CalendarDayChip: View {
    var day: Date
    var isSelected: Bool
    var isEnabled = true
    var eventCount: Int
    var previewColors: [Color]

    private var isToday: Bool {
        CalendarSchedule.calendar.isDateInToday(day)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(day.formatted(.dateTime.weekday(.narrow)))
                .font(.caption.weight(.semibold))
                .textCase(.uppercase)

            Text(day.formatted(.dateTime.day()))
                .font(.title3.weight(.bold))

            HStack(spacing: 4) {
                if isEnabled {
                    ForEach(Array(previewColors.enumerated()), id: \.offset) { _, color in
                        Circle()
                            .fill(isSelected ? Color.white.opacity(0.92) : color)
                            .frame(width: 6, height: 6)
                    }

                    if eventCount > previewColors.count {
                        Text("+\(eventCount - previewColors.count)")
                            .font(.caption2.weight(.semibold))
                            .foregroundStyle(isSelected ? Color.white.opacity(0.92) : .secondary)
                    }
                } else {
                    Capsule()
                        .fill(Color.secondary.opacity(0.18))
                        .frame(width: 14, height: 4)
                }
            }

            Text(day.formatted(.dateTime.month(.abbreviated)))
                .font(.caption2)
                .foregroundStyle(textColor.opacity(0.72))
        }
        .frame(width: 64, alignment: .leading)
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(backgroundStyle, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(borderColor, lineWidth: isToday && !isSelected ? 1.5 : 1)
        }
        .foregroundStyle(textColor)
    }

    private var textColor: Color {
        if isSelected { return .white }
        if !isEnabled { return .secondary }
        return isToday ? .accentColor : .primary
    }

    private var backgroundStyle: Color {
        if isSelected { return .accentColor }
        return isEnabled ? Color(uiColor: .secondarySystemBackground) : Color(uiColor: .tertiarySystemBackground)
    }

    private var borderColor: Color {
        if isSelected { return .accentColor }
        if !isEnabled { return Color.primary.opacity(0.04) }
        if isToday { return .accentColor.opacity(0.45) }
        return Color.primary.opacity(0.06)
    }
}

struct CalendarStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}
