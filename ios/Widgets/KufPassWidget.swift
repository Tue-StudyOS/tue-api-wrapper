import SwiftUI
import WidgetKit

struct KufPassWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "KufPassWidget", provider: KufPassProvider()) { _ in
            KufPassWidgetView()
                .widgetURL(AppLink.kufPass.url)
                .containerBackground(for: .widget) {
                    Color.accentColor.opacity(0.08)
                }
        }
        .configurationDisplayName("KuF Pass")
        .description("Open your saved KuF barcode at the entrance.")
        .supportedFamilies([.systemSmall, .accessoryCircular, .accessoryRectangular])
    }
}

private struct KufPassEntry: TimelineEntry {
    var date: Date
}

private struct KufPassProvider: TimelineProvider {
    func placeholder(in context: Context) -> KufPassEntry {
        KufPassEntry(date: .now)
    }

    func getSnapshot(in context: Context, completion: @escaping (KufPassEntry) -> Void) {
        completion(placeholder(in: context))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<KufPassEntry>) -> Void) {
        completion(Timeline(entries: [placeholder(in: context)], policy: .never))
    }
}

private struct KufPassWidgetView: View {
    @Environment(\.widgetFamily) private var family

    var body: some View {
        switch family {
        case .accessoryCircular:
            ZStack {
                AccessoryWidgetBackground()
                Image(systemName: "barcode")
                    .font(.title3)
            }
            .accessibilityLabel("Open KuF pass")
        case .accessoryRectangular:
            Label("KuF pass", systemImage: "barcode")
                .font(.headline)
        default:
            VStack(alignment: .leading, spacing: 6) {
                Image(systemName: "barcode")
                    .font(.title)
                    .foregroundStyle(Color.accentColor)
                    .widgetAccentable()
                Spacer(minLength: 6)
                Text("KuF pass").font(.headline)
                Text("Open barcode").font(.caption).foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        }
    }
}
