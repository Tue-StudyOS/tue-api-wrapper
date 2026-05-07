import XCTest
@testable import TueAPI

final class SeatfinderClientTests: XCTestCase {
    func testParsesSeatfinderPayloadIntoCampusSeatAvailability() throws {
        let payload = """
        [{
          "seatestimate": {
            "UBH1": [{
              "timestamp": {"date": "2026-05-06 09:15:00.000000"},
              "free_seats": "160",
              "occupied_seats": "8"
            }]
          }
        }, {
          "location": {
            "UBH1": [{
              "timestamp": {"date": "2026-05-06 09:00:00.000000"},
              "name": "UB Hauptgebäude",
              "long_name": "University Library Main Building",
              "available_seats": "168",
              "level": "1",
              "building": "UB",
              "room": "H1",
              "url": "https://uni-tuebingen.de/library"
            }]
          }
        }]
        """.data(using: .utf8)!

        let availability = try SeatfinderClient.parse(
            payload,
            sourceURL: URL(string: "https://seatfinder.bibliothek.kit.edu/tuebingen/getdata.php")!,
            retrievedAt: Date(timeIntervalSince1970: 1_777_777_777)
        )

        XCTAssertEqual(availability.locations.count, 1)
        XCTAssertEqual(availability.locations[0].locationID, "UBH1")
        XCTAssertEqual(availability.locations[0].name, "UB Hauptgebäude")
        XCTAssertEqual(availability.locations[0].totalSeats, 168)
        XCTAssertEqual(availability.locations[0].freeSeats, 160)
        XCTAssertEqual(availability.locations[0].occupiedSeats, 8)
        XCTAssertEqual(availability.locations[0].occupancyPercent, 4.8)
    }

    func testParsesJSONPSeatfinderPayload() throws {
        let payload = """
        callback([{"seatestimate":{}},{"location":{}}]);
        """.data(using: .utf8)!

        let availability = try SeatfinderClient.parse(
            payload,
            sourceURL: URL(string: "https://example.com/seats")!
        )

        XCTAssertEqual(availability.locations.count, 0)
    }
}
