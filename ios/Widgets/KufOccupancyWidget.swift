import SwiftUI
import WidgetKit

struct KufOccupancyEntry: TimelineEntry {
    let date: Date
    let occupancy: KufTrainingOccupancy?
    let errorMessage: String?
}

struct KufOccupancyProvider: TimelineProvider {
    func placeholder(in context: Context) -> KufOccupancyEntry {
        KufOccupancyEntry(date: Date(), occupancy: nil, errorMessage: nil)
    }

    func getSnapshot(in context: Context, completion: @escaping @Sendable (KufOccupancyEntry) -> Void) {
        Task {
            completion(await loadEntry())
        }
    }

    func getTimeline(in context: Context, completion: @escaping @Sendable (Timeline<KufOccupancyEntry>) -> Void) {
        Task {
            let entry = await loadEntry()
            let refreshSeconds = entry.occupancy?.refreshAfterSeconds ?? 900
            let nextDate = Date().addingTimeInterval(TimeInterval(max(300, refreshSeconds)))
            completion(Timeline(entries: [entry], policy: .after(nextDate)))
        }
    }

    private func loadEntry() async -> KufOccupancyEntry {
        guard let client = KufOccupancyClient() else {
            return KufOccupancyEntry(date: Date(), occupancy: nil, errorMessage: "Backend URL is not configured.")
        }
        do {
            let occupancy = try await client.fetchOccupancy()
            KufOccupancyHistoryStore()?.record(occupancy)
            return KufOccupancyEntry(date: Date(), occupancy: occupancy, errorMessage: nil)
        } catch {
            return KufOccupancyEntry(date: Date(), occupancy: nil, errorMessage: error.localizedDescription)
        }
    }
}

struct KufOccupancyWidget: Widget {
    let kind = "KufOccupancyWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: KufOccupancyProvider()) { entry in
            KufOccupancyWidgetView(entry: entry)
                .containerBackground(.background, for: .widget)
        }
        .configurationDisplayName("KuF Count")
        .description("Shows the current Kraft und Fitnesshalle training count.")
        .supportedFamilies([.systemSmall])
    }
}

private struct KufOccupancyWidgetView: View {
    let entry: KufOccupancyEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("KuF")
                .font(.headline)
            Spacer(minLength: 0)
            if let occupancy = entry.occupancy {
                Text("\(occupancy.count)")
                    .font(.system(size: 48, weight: .semibold, design: .rounded))
                    .minimumScaleFactor(0.7)
                Text("training now")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                Text("No count")
                    .font(.title3.weight(.semibold))
                Text(entry.errorMessage ?? "Refresh later.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
            }
            Spacer(minLength: 0)
            Text(entry.date, style: .time)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}
