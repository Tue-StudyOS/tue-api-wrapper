import MapKit
import SwiftUI

struct CampusSeatMap: View {
    let locations: [CampusSeatLocation]
    @State private var position: MapCameraPosition = .automatic
    @State private var selection: CampusSeatMapPoint?
    @State private var clusters: [CampusSeatMapCluster] = []
    @State private var camera: MapCamera?
    @ScaledMetric(relativeTo: .caption) private var markerWidth = 100.0
    @ScaledMetric(relativeTo: .caption) private var markerHeight = 44.0
    @Environment(\.colorScheme) private var colorScheme

    private var pins: [CampusSeatMapPin] { CampusSeatMapPin.grouped(locations) }
    private var selectedPin: CampusSeatMapPin? { pins.first { $0.id == selection } }

    var body: some View {
        if pins.isEmpty {
            AppSurfaceCard {
                ContentUnavailableView("No mapped study spaces", systemImage: "map", description: Text("Seatfinder did not provide map locations. Open List to see all study spaces."))
            }
        } else {
            map

            HStack {
                Menu("Find an area", systemImage: "magnifyingglass") {
                    ForEach(pins) { pin in
                        ForEach(pin.locations) { location in
                            Button(location.longName ?? location.name) { focus(pin) }
                        }
                    }
                }
                Spacer()
                Button("Show all", systemImage: "arrow.up.left.and.down.right", action: showOverview)
            }
            .font(.subheadline.weight(.semibold))

            if let pin = selectedPin {
                ForEach(pin.locations) { CampusSeatLocationCard(location: $0) }
            } else {
                Text("Free / total seats · Tap a group to zoom in. The bar shows how full it is.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var map: some View {
        GeometryReader { geometry in
            MapReader { proxy in
                Map(position: $position) {
                    UserAnnotation()
                    if let selectedPin {
                        annotation(selectedPin, siteCount: 1) { focus(selectedPin) }
                    } else {
                        ForEach(clusters) { cluster in
                            let nearby = pins.filter { cluster.points.contains($0.id) }
                            if let pin = nearby.first {
                                let summary = CampusSeatMapPin(id: pin.id, locations: nearby.flatMap(\.locations))
                                annotation(summary, siteCount: nearby.count) {
                                    if nearby.count == 1 { focus(pin) }
                                    else { zoom(to: nearby) }
                                }
                            }
                        }
                    }
                }
                .mapStyle(.standard(elevation: .realistic, pointsOfInterest: .excludingAll))
                .mapControls {
                    MapUserLocationButton()
                    MapCompass()
                    MapPitchToggle()
                }
                .onMapCameraChange(frequency: .continuous) { context in
                    camera = context.camera
                    updateClusters(using: proxy)
                }
                .onChange(of: geometry.size) { updateClusters(using: proxy) }
                .onChange(of: pins.map(\.id)) { updateClusters(using: proxy) }
                .onChange(of: markerWidth) { updateClusters(using: proxy) }
            }
        }
        .frame(height: 390)
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .onAppear(perform: showOverview)
        .sensoryFeedback(.selection, trigger: selection) { _, newValue in newValue != nil }
    }

    private func updateClusters(using proxy: MapProxy) {
        let layout = CampusSeatMapCluster.layout(
            pins.map(\.id), badgeSize: CGSize(width: markerWidth + 8, height: markerHeight + 8)
        ) { proxy.convert($0.coordinate, to: .local) }
        if layout.map(\.points) != clusters.map(\.points) { clusters = layout }
    }

    private func annotation(_ pin: CampusSeatMapPin, siteCount: Int, action: @escaping () -> Void) -> some MapContent {
        let name = siteCount > 1 ? "\(siteCount) nearby locations" : pin.name
        return Annotation(name, coordinate: pin.id.coordinate, anchor: .bottom) {
            Button(action: action) {
                seatMarker(pin, grouped: siteCount > 1)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("\(name), \(pin.seatLabel)")
            .accessibilityHint(siteCount > 1 ? "Zooms in to show individual locations" : "Shows seat details")
            .accessibilityAddTraits(selection == pin.id ? .isSelected : [])
        }
        .annotationTitles(.hidden)
    }

    private func zoom(to nearby: [CampusSeatMapPin]) {
        let bounds = mapBounds(nearby)
        let center = MKMapPoint(x: bounds.midX, y: bounds.midY).coordinate
        position = .camera(MapCamera(centerCoordinate: center, distance: max(35, (camera?.distance ?? 850) * 0.45),
                                     heading: camera?.heading ?? 18, pitch: camera?.pitch ?? 52))
    }

    private func focus(_ pin: CampusSeatMapPin) {
        selection = pin.id
        position = .camera(MapCamera(centerCoordinate: pin.id.coordinate, distance: 675, heading: 22, pitch: 57))
    }

    private func seatMarker(_ pin: CampusSeatMapPin, grouped: Bool) -> some View {
        let selected = selection == pin.id
        return VStack(spacing: 3) {
            HStack(spacing: 4) {
                Image(systemName: grouped ? "square.stack.fill" : pin.freeSeats == 0 ? "chair" : "chair.fill")
                if let total = pin.totalSeats {
                    let free = pin.freeSeats?.formatted() ?? "–"
                    Text("\(free)/\(total.formatted())").monospacedDigit()
                } else if let free = pin.freeSeats {
                    Text("\(free.formatted()) free").monospacedDigit()
                } else {
                    Text("–")
                }
            }
            .lineLimit(1)
            .minimumScaleFactor(0.7)
            if let occupancy = pin.occupancy {
                occupancyBar(occupancy)
            }
        }
        .font(.caption.weight(.bold))
        .foregroundStyle(Color.primary)
        .padding(.horizontal, 8)
        .frame(width: markerWidth, height: markerHeight)
        .background(Color(uiColor: .systemBackground), in: Capsule())
        .overlay { Capsule().strokeBorder(selected ? Color.accentColor : Color.primary.opacity(colorScheme == .dark ? 0.55 : 0.26), lineWidth: selected ? 2 : 1) }
        .shadow(color: .black.opacity(0.22), radius: 4, y: 2)
    }

    private func occupancyBar(_ occupancy: Double) -> some View {
        let tint: Color = occupancy >= 0.85 ? .red : occupancy >= 0.60 ? .orange : .green
        return Capsule()
            .fill(Color.primary.opacity(colorScheme == .dark ? 0.36 : 0.18))
            .overlay(alignment: .leading) {
                Capsule().fill(tint).frame(width: 32 * occupancy)
            }
            .frame(width: 32, height: 3)
            .accessibilityHidden(true)
    }

    private func showOverview() {
        selection = nil
        let bounds = mapBounds(pins)
        guard !bounds.isNull else { return }
        let center = MKMapPoint(x: bounds.midX, y: bounds.midY).coordinate
        // Leave room for the full badge on either side of the map at city scale.
        let distance = max(850, max(bounds.width, bounds.height) * MKMetersPerMapPointAtLatitude(center.latitude) * 3.8)
        position = .camera(MapCamera(centerCoordinate: center, distance: distance, heading: 18, pitch: 52))
    }

    private func mapBounds(_ pins: [CampusSeatMapPin]) -> MKMapRect {
        pins.map { MKMapPoint($0.id.coordinate) }.reduce(.null) {
            $0.union(MKMapRect(origin: $1, size: .init(width: 1, height: 1)))
        }
    }
}
