import WidgetKit
import SwiftUI

struct UpcomingLecturesEntry: TimelineEntry {
    let date: Date
    let snapshot: LectureSnapshot?
    var showLockScreenDetails = LectureWidgetPrivacy.showsDetails
}

struct UpcomingLecturesProvider: TimelineProvider {
    func placeholder(in context: Context) -> UpcomingLecturesEntry {
        UpcomingLecturesEntry(date: Date(), snapshot: nil)
    }

    func getSnapshot(in context: Context, completion: @escaping @Sendable (UpcomingLecturesEntry) -> Void) {
        completion(UpcomingLecturesEntry(date: Date(), snapshot: UpcomingLectureCache.load()))
    }

    func getTimeline(in context: Context, completion: @escaping @Sendable (Timeline<UpcomingLecturesEntry>) -> Void) {
        let now = Date()
        let snapshot = UpcomingLectureCache.load()
        let refresh = now.addingTimeInterval(1800)
        let dates = LectureWidgetSchedule.entryDates(snapshot?.events ?? [], from: now, until: refresh)
        let entries = dates.map { UpcomingLecturesEntry(date: $0, snapshot: snapshot) }
        completion(Timeline(entries: entries, policy: .after(refresh)))
    }
}

struct UpcomingLecturesWidget: Widget {
    let kind = "UpcomingLecturesWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: UpcomingLecturesProvider()) { entry in
            UpcomingLecturesWidgetView(entry: entry)
                .widgetURL(AppLink.schedule.url)
        }
        .configurationDisplayName("Upcoming Lectures")
        .description("See your next lectures and open your schedule.")
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryRectangular, .accessoryInline, .accessoryCircular])
    }
}

struct UpcomingLecturesWidgetView: View {
    @Environment(\.widgetFamily) private var family
    let entry: UpcomingLecturesEntry

    var body: some View {
        switch family {
        case .accessoryRectangular:
            AccessoryLectureView(event: nextEvent, showsDetails: entry.showLockScreenDetails)
                .containerBackground(.clear, for: .widget)
        case .accessoryInline:
            if let nextEvent {
                let time = nextEvent.startDate.formatted(date: .omitted, time: .shortened)
                Text(entry.showLockScreenDetails ? "\(nextEvent.title) · \(time)" : "Next lecture · \(time)")
                    .containerBackground(.clear, for: .widget)
            } else {
                Text("No upcoming lectures").containerBackground(.clear, for: .widget)
            }
        case .accessoryCircular:
            if let nextEvent {
                VStack {
                    Image(systemName: "calendar")
                    Text(nextEvent.startDate, style: .time).font(.caption2)
                }
                .containerBackground(.clear, for: .widget)
            } else {
                Image(systemName: "calendar").containerBackground(.clear, for: .widget)
            }
        default:
            WidgetLectureListView(snapshot: entry.snapshot, events: upcomingEvents, compact: family == .systemSmall)
                .containerBackground(.background, for: .widget)
        }
    }

    private var nextEvent: LectureEvent? {
        upcomingEvents.first
    }

    private var upcomingEvents: [LectureEvent] {
        LectureWidgetSchedule.upcoming(entry.snapshot?.events ?? [], at: entry.date)
    }
}

struct WidgetLectureListView: View {
    let snapshot: LectureSnapshot?
    let events: [LectureEvent]
    let compact: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("TUE API")
                .font(.headline)

            if let snapshot, let first = events.first {
                WidgetLectureRow(event: first)
                if !compact {
                    ForEach(events.dropFirst().prefix(2)) { event in
                        Divider()
                        WidgetLectureRow(event: event)
                    }
                }
                Text("Checked \(snapshot.refreshedAt.formatted(date: .abbreviated, time: .shortened))")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                if let semesterCredits = snapshot.semesterCredits, !compact {
                    Text(semesterCredits.displayText)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text(snapshot == nil ? "No cached lectures" : "No upcoming lectures")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text("Open the app and refresh Alma.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
    }
}

struct WidgetLectureRow: View {
    let event: LectureEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(event.title)
                .font(.subheadline)
                .lineLimit(2)
            Text(event.timeRangeText)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

struct AccessoryLectureView: View {
    let event: LectureEvent?
    let showsDetails: Bool

    var body: some View {
        if let event {
            VStack(alignment: .leading) {
                Text(showsDetails ? event.title : "Next lecture")
                    .lineLimit(1)
                Text(event.startDate, style: .time)
                    .font(.caption2)
                if showsDetails, let location = event.location {
                    Text(location).font(.caption2).lineLimit(1)
                }
            }
        } else {
            Text("No cached lectures")
        }
    }
}
