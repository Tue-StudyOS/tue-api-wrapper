import WidgetKit
import SwiftUI

struct UpcomingLecturesEntry: TimelineEntry {
    let date: Date
    let snapshot: LectureSnapshot?
}

struct UpcomingLecturesProvider: TimelineProvider {
    func placeholder(in context: Context) -> UpcomingLecturesEntry {
        UpcomingLecturesEntry(date: Date(), snapshot: nil)
    }

    func getSnapshot(in context: Context, completion: @escaping (UpcomingLecturesEntry) -> Void) {
        completion(UpcomingLecturesEntry(date: Date(), snapshot: UpcomingLectureCache.load()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<UpcomingLecturesEntry>) -> Void) {
        let entry = UpcomingLecturesEntry(date: Date(), snapshot: UpcomingLectureCache.load())
        let next = Calendar.current.date(byAdding: .minute, value: 30, to: Date()) ?? Date().addingTimeInterval(1800)
        completion(Timeline(entries: [entry], policy: .after(next)))
    }
}

struct UpcomingLecturesWidget: Widget {
    let kind = "UpcomingLecturesWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: UpcomingLecturesProvider()) { entry in
            UpcomingLecturesWidgetView(entry: entry)
        }
        .configurationDisplayName("Upcoming Lectures")
        .description("Shows cached Alma lectures refreshed by the TUE API app.")
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryRectangular])
    }
}

struct UpcomingLecturesWidgetView: View {
    @Environment(\.widgetFamily) private var family
    let entry: UpcomingLecturesEntry

    var body: some View {
        switch family {
        case .accessoryRectangular:
            AccessoryLectureView(event: nextEvent)
        default:
            WidgetLectureListView(snapshot: entry.snapshot, compact: family == .systemSmall)
                .containerBackground(.background, for: .widget)
        }
    }

    private var nextEvent: LectureEvent? {
        upcomingEvents.first
    }

    private var upcomingEvents: [LectureEvent] {
        entry.snapshot?.events.filter { !$0.isCancelled && ($0.endDate ?? $0.startDate) >= Date() } ?? []
    }
}

struct WidgetLectureListView: View {
    let snapshot: LectureSnapshot?
    let compact: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("TUE API")
                .font(.headline)

            let events = snapshot?.events.filter { !$0.isCancelled && ($0.endDate ?? $0.startDate) >= Date() } ?? []
            if let snapshot, let first = events.first {
                WidgetLectureRow(event: first)
                if !compact {
                    ForEach(events.dropFirst().prefix(2)) { event in
                        Divider()
                        WidgetLectureRow(event: event)
                    }
                }
                Text(snapshot.sourceTerm)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                if let semesterCredits = snapshot.semesterCredits, !compact {
                    Text(semesterCredits.displayText)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text("No cached lectures")
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

    var body: some View {
        if let event {
            VStack(alignment: .leading) {
                Text(event.title)
                    .lineLimit(1)
                Text(event.timeRangeText)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        } else {
            Text("No cached lectures")
        }
    }
}
