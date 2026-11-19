import CoreLocation
import Foundation

struct CampusSeatMapPoint: Hashable {
    let latitude: Double
    let longitude: Double

    init?(_ value: String?) {
        guard let value else { return nil }
        let fields = value.split(separator: ";", omittingEmptySubsequences: false)
        guard fields.count == 2,
              let latitude = Double(fields[0].trimmingCharacters(in: .whitespaces)),
              let longitude = Double(fields[1].trimmingCharacters(in: .whitespaces)),
              CLLocationCoordinate2DIsValid(.init(latitude: latitude, longitude: longitude)) else { return nil }
        self.latitude = latitude
        self.longitude = longitude
    }

    var coordinate: CLLocationCoordinate2D { .init(latitude: latitude, longitude: longitude) }
}

struct CampusSeatMapPin: Identifiable {
    let id: CampusSeatMapPoint
    let locations: [CampusSeatLocation]

    var name: String {
        guard let first = locations.first else { return "Study space" }
        if locations.count == 1 { return first.longName ?? first.name }
        return first.building ?? "Study spaces"
    }

    var freeSeats: Int? {
        sum(\.freeSeats)
    }

    var totalSeats: Int? {
        sum(\.totalSeats)
    }

    var occupancy: Double? {
        guard let freeSeats, let totalSeats, totalSeats > 0, freeSeats <= totalSeats else { return nil }
        return Double(totalSeats - freeSeats) / Double(totalSeats)
    }

    var seatLabel: String {
        if let freeSeats, let totalSeats { return "\(freeSeats) of \(totalSeats) seats free" }
        if let freeSeats { return "\(freeSeats) free" }
        if let totalSeats { return "\(totalSeats) seats, free count unavailable" }
        return locations.count == 1 ? "Count unavailable" : "\(locations.count) areas"
    }

    private func sum(_ keyPath: KeyPath<CampusSeatLocation, Int?>) -> Int? {
        let counts = locations.compactMap { $0[keyPath: keyPath] }
        guard !counts.isEmpty, counts.count == locations.count, counts.allSatisfy({ $0 >= 0 }) else { return nil }
        return counts.reduce(0, +)
    }

    static func grouped(_ locations: [CampusSeatLocation]) -> [Self] {
        var byPoint: [CampusSeatMapPoint: [CampusSeatLocation]] = [:]
        for location in locations {
            guard let point = CampusSeatMapPoint(location.geoCoordinates) else { continue }
            byPoint[point, default: []].append(location)
        }
        return byPoint.map { Self(id: $0.key, locations: $0.value) }
            .sorted { ($0.id.latitude, $0.id.longitude) < ($1.id.latitude, $1.id.longitude) }
    }
}
