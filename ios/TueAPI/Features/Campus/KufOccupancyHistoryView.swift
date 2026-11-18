import Charts
import SwiftUI

struct KufOccupancyHistoryView: View {
    private let store: KufOccupancyHistoryStore?

    @State private var records: [KufOccupancyHistoryRecord] = []
    @State private var selectedScope: KufOccupancyHistoryScope = .hour

    init(store: KufOccupancyHistoryStore? = KufOccupancyHistoryStore()) {
        self.store = store
    }

    var body: some View {
        List {
            Section {
                Picker("Trend grouping", selection: $selectedScope) {
                    ForEach(KufOccupancyHistoryScope.allCases) { scope in
                        Text(scope.title).tag(scope)
                    }
                }
                .pickerStyle(.segmented)

                if chartPoints.isEmpty {
                    ContentUnavailableView(
                        "No KuF history yet",
                        systemImage: "chart.bar.xaxis",
                        description: Text("Keep the KuF widget active to record up to one local sample per hour.")
                    )
                } else {
                    Chart(chartPoints) { point in
                        BarMark(
                            x: .value(selectedScope.axisTitle, point.label),
                            y: .value("Average count", point.average)
                        )
                        .foregroundStyle(.tint)
                    }
                    .chartYAxis {
                        AxisMarks(position: .leading)
                    }
                    .frame(height: 220)

                    Text("Average training count from local hourly samples.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }

            Section("History") {
                LabeledContent("Samples", value: "\(records.count)")
                if let latest = records.last {
                    LabeledContent("Latest", value: "\(latest.count)")
                    LabeledContent("Updated", value: Self.dateFormatter.string(from: latest.recordedAt))
                }
            }

            if !records.isEmpty {
                Section("Recent samples") {
                    ForEach(records.suffix(8).reversed()) { record in
                        LabeledContent {
                            Text("\(record.count)")
                        } label: {
                            Text(Self.dateFormatter.string(from: record.recordedAt))
                        }
                    }
                }
            }
        }
        .navigationTitle("KuF trends")
        .onAppear(perform: loadHistory)
        .refreshable {
            loadHistory()
        }
    }

    private var chartPoints: [KufOccupancyChartPoint] {
        selectedScope.points(from: records, calendar: .current)
    }

    private func loadHistory() {
        records = store?.loadRecords() ?? []
    }

    private static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()
}

private enum KufOccupancyHistoryScope: String, CaseIterable, Identifiable {
    case hour
    case weekday

    var id: Self { self }

    var title: String {
        switch self {
        case .hour:
            "Time"
        case .weekday:
            "Weekday"
        }
    }

    var axisTitle: String {
        switch self {
        case .hour:
            "Hour"
        case .weekday:
            "Weekday"
        }
    }

    func points(
        from records: [KufOccupancyHistoryRecord],
        calendar: Calendar
    ) -> [KufOccupancyChartPoint] {
        let grouped = Dictionary(grouping: records) { record in
            switch self {
            case .hour:
                calendar.component(.hour, from: record.hourStartedAt)
            case .weekday:
                calendar.component(.weekday, from: record.hourStartedAt)
            }
        }

        return bucketOrder.compactMap { bucket in
            guard let values = grouped[bucket]?.map(\.count), !values.isEmpty else {
                return nil
            }
            let average = Double(values.reduce(0, +)) / Double(values.count)
            return KufOccupancyChartPoint(
                id: "\(rawValue)-\(bucket)",
                label: label(for: bucket),
                average: average,
                sampleCount: values.count
            )
        }
    }

    private var bucketOrder: [Int] {
        switch self {
        case .hour:
            Array(0...23)
        case .weekday:
            [2, 3, 4, 5, 6, 7, 1]
        }
    }

    private func label(for bucket: Int) -> String {
        switch self {
        case .hour:
            "\(bucket)"
        case .weekday:
            Self.weekdayLabels[bucket] ?? "\(bucket)"
        }
    }

    private static let weekdayLabels = [
        1: "Sun",
        2: "Mon",
        3: "Tue",
        4: "Wed",
        5: "Thu",
        6: "Fri",
        7: "Sat"
    ]
}

private struct KufOccupancyChartPoint: Identifiable {
    var id: String
    var label: String
    var average: Double
    var sampleCount: Int
}
