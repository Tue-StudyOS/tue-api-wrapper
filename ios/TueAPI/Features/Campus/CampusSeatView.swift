import SwiftUI

struct CampusSeatView: View {
    @State private var phase: CampusSeatLoadPhase = .idle
    @State private var availability: CampusSeatAvailability?
    @State private var display: CampusSeatDisplay = .list

    private var locations: [CampusSeatLocation] {
        (availability?.locations ?? []).sorted {
            let leftFree = $0.freeSeats ?? -1
            let rightFree = $1.freeSeats ?? -1
            return leftFree == rightFree ? $0.name < $1.name : leftFree > rightFree
        }
    }

    private var subtitle: String {
        if let availability, !availability.locations.isEmpty {
            return "\(availability.locations.count) University Library areas with live seat counts"
        }
        return "Live public seat availability from the Tübingen seatfinder"
    }

    private var statusLine: CampusSeatStatusLine? {
        switch phase {
        case .loading where availability != nil:
            CampusSeatStatusLine(text: "Refreshing library seat availability.", tint: .accentColor, isLoading: true)
        case .failed(let message):
            CampusSeatStatusLine(text: message, systemImage: "exclamationmark.triangle", tint: .orange)
        default:
            nil
        }
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                StudentScreenHeading(title: "Study spaces", detail: subtitle)

                if let statusLine {
                    AppInlineStatusLine(
                        text: statusLine.text,
                        systemImage: statusLine.systemImage,
                        tint: statusLine.tint,
                        isLoading: statusLine.isLoading
                    )
                }

                if !locations.isEmpty {
                    Picker("Study spaces view", selection: $display) {
                        Label("List", systemImage: "list.bullet").tag(CampusSeatDisplay.list)
                        Label("3D map", systemImage: "map").tag(CampusSeatDisplay.map)
                    }
                    .pickerStyle(.segmented)
                }

                if display == .map && !locations.isEmpty {
                    CampusSeatMap(locations: locations)
                } else {
                    content
                }

                if let availability {
                    Text("Last updated \(formatTimestamp(availability.retrievedAt))")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)
                }
            }
            .padding(16)
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .sensoryFeedback(.selection, trigger: display)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refreshSeats() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(phase.isLoading)
            }
        }
        .refreshable {
            await refreshSeats()
        }
        .task {
            if availability == nil {
                await refreshSeats()
            }
        }
    }

    @ViewBuilder
    private var content: some View {
        if phase.isLoading && availability == nil {
            VStack(spacing: 12) {
                ForEach(0..<4, id: \.self) { _ in
                    CampusSeatSkeletonCard()
                }
            }
        } else if locations.isEmpty {
            AppSurfaceCard {
                ContentUnavailableView(
                    unavailableTitle,
                    systemImage: unavailableSystemImage,
                    description: Text(unavailableDescription)
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 28)
            }
        } else {
            VStack(spacing: 12) {
                ForEach(locations) { location in
                    CampusSeatLocationCard(location: location)
                }
            }
        }
    }

    private var unavailableTitle: String {
        switch phase {
        case .failed:
            "Could not load seats"
        default:
            "No seat data"
        }
    }

    private var unavailableSystemImage: String {
        switch phase {
        case .failed:
            "exclamationmark.triangle"
        default:
            "chair"
        }
    }

    private var unavailableDescription: String {
        switch phase {
        case .failed(let message):
            message
        default:
            "The public seatfinder did not return any University Library areas."
        }
    }

    private func refreshSeats() async {
        phase = .loading
        do {
            availability = try await SeatfinderClient().fetchAvailability()
            phase = .loaded(Date())
        } catch is CancellationError {
            if availability == nil {
                phase = .idle
            }
        } catch let error as URLError where error.code == .cancelled {
            if availability == nil {
                phase = .idle
            }
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

private struct CampusSeatStatusLine {
    let text: String
    var systemImage: String? = nil
    var tint: Color = .secondary
    var isLoading = false
}

struct CampusSeatLocationCard: View {
    let location: CampusSeatLocation

    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 14) {
                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(location.longName ?? location.name)
                            .font(.headline)
                        Text(detailLine)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Spacer(minLength: 0)
                    if let url = validURL(location.url) {
                        Link(destination: url) {
                            Label("Open", systemImage: "arrow.up.forward.square")
                        }
                        .font(.footnote.weight(.semibold))
                    }
                }

                if let occupancy = location.occupancyPercent {
                    ProgressView(value: min(max(occupancy / 100, 0), 1))
                        .tint(occupancyTint)
                        .accessibilityLabel("Seat occupancy")
                }

                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 8) { metrics }
                    VStack(alignment: .leading, spacing: 8) { metrics }
                }
            }
        }
    }

    @ViewBuilder private var metrics: some View {
        CampusSeatMetricPill(label: "Free", value: metricText(location.freeSeats), tint: .green.opacity(0.16))
        CampusSeatMetricPill(label: "Occupied", value: metricText(location.occupiedSeats), tint: .orange.opacity(0.16))
        CampusSeatMetricPill(label: "Capacity", value: metricText(location.totalSeats), tint: .secondary.opacity(0.14))
    }

    private var detailLine: String {
        guard location.freeSeats != nil || location.occupiedSeats != nil else {
            return "Seat count unavailable"
        }
        if let updatedAt = location.updatedAt {
            return "Updated \(formatTimestamp(updatedAt))"
        }
        return "University Library seatfinder"
    }

    private var occupancyTint: Color {
        guard let percent = location.occupancyPercent else { return .secondary }
        if percent >= 85 { return .red }
        if percent >= 60 { return .orange }
        return .green
    }
}

private enum CampusSeatDisplay: Hashable {
    case list, map
}

private struct CampusSeatMetricPill: View {
    let label: String
    let value: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.caption)
            Text(value)
                .font(.footnote.weight(.semibold))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(tint, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

private struct CampusSeatSkeletonCard: View {
    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 12) {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Color.secondary.opacity(0.14))
                    .frame(width: 220, height: 18)
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Color.secondary.opacity(0.1))
                    .frame(height: 12)
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Color.secondary.opacity(0.1))
                    .frame(width: 180, height: 28)
            }
        }
        .redacted(reason: .placeholder)
    }
}

private func metricText(_ value: Int?) -> String {
    guard let value else { return "n/a" }
    return "\(value)"
}

private func validURL(_ value: String?) -> URL? {
    guard let value, !value.isEmpty else {
        return nil
    }
    return URL(string: value)
}

private func formatTimestamp(_ value: String) -> String {
    guard let date = ISO8601DateFormatter().date(from: value) else {
        return value
    }
    return date.formatted(date: .abbreviated, time: .shortened)
}
