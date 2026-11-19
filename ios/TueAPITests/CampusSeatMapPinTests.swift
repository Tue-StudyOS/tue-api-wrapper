import Foundation
import XCTest
@testable import TueAPI

final class CampusSeatMapPinTests: XCTestCase {
    func testOnlyValidLocationsAppearAndFloorsShareAPin() throws {
        let locations = try decode("""
        [
          {"location_id":"A1","name":"First floor","geo_coordinates":"48.52539;9.06189","free_seats":6,"total_seats":8},
          {"location_id":"A2","name":"Second floor","geo_coordinates":"48.52539;9.06189","free_seats":4,"total_seats":12},
          {"location_id":"B1","name":"Another library","geo_coordinates":"48.53658;9.03623","free_seats":3},
          {"location_id":"C1","name":"Unmapped","geo_coordinates":"999;9.06189","free_seats":50}
        ]
        """)

        let pins = CampusSeatMapPin.grouped(locations)
        XCTAssertEqual(pins.count, 2)
        XCTAssertEqual(pins.first?.locations.map(\.id), ["A1", "A2"])
        XCTAssertEqual(pins.first?.freeSeats, 10)
        XCTAssertEqual(pins.first?.totalSeats, 20)
        XCTAssertEqual(pins.first?.occupancy, 0.5)
        XCTAssertNil(pins.last?.occupancy)
    }

    func testMissingSeatCountDoesNotBecomeZeroOrAPartialTotal() throws {
        let locations = try decode("""
        [
          {"location_id":"A1","name":"First floor","geo_coordinates":"48.52539;9.06189","free_seats":6,"total_seats":8},
          {"location_id":"A2","name":"Second floor","geo_coordinates":"48.52539;9.06189","total_seats":12}
        ]
        """)

        let pin = try XCTUnwrap(CampusSeatMapPin.grouped(locations).first)
        XCTAssertNil(pin.freeSeats)
        XCTAssertEqual(pin.totalSeats, 20)
        XCTAssertNil(pin.occupancy)
        XCTAssertEqual(pin.seatLabel, "20 seats, free count unavailable")
    }

    func testOverlappingBadgesGroupAndSeparateWhenZoomedIn() throws {
        let a = try XCTUnwrap(CampusSeatMapPoint("48.52;9.06"))
        let b = try XCTUnwrap(CampusSeatMapPoint("48.53;9.06"))
        let c = try XCTUnwrap(CampusSeatMapPoint("48.54;9.06"))
        let badge = CGSize(width: 108, height: 52)

        let overview = CampusSeatMapCluster.layout([a, b, c], badgeSize: badge) {
            [a: CGPoint(x: 60, y: 50), b: CGPoint(x: 130, y: 75), c: CGPoint(x: 150, y: 120)][$0]
        }
        XCTAssertEqual(overview.map(\.points), [[a, b], [c]])

        let zoomed = CampusSeatMapCluster.layout([a, b, c], badgeSize: badge) {
            [a: CGPoint(x: 60, y: 50), b: CGPoint(x: 190, y: 50), c: CGPoint(x: 200, y: 140)][$0]
        }
        XCTAssertEqual(zoomed.map(\.points), [[a], [b], [c]])
    }

    private func decode(_ payload: String) throws -> [CampusSeatLocation] {
        try JSONDecoder().decode([CampusSeatLocation].self, from: Data(payload.utf8))
    }
}
