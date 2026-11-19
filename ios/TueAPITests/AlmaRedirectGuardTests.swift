import Foundation
import XCTest
@testable import TueAPI

final class AlmaRedirectGuardTests: XCTestCase {
    func testAcceptsOfficialAlmaPages() {
        let origin = AlmaClient.officialBaseURL

        XCTAssertTrue(AlmaRedirectGuard.matches(origin.appending(path: "alma"), origin: origin))
        XCTAssertTrue(AlmaRedirectGuard.matches(URL(string: "https://alma.uni-tuebingen.de:443/alma")!, origin: origin))
    }

    func testRejectsUnapprovedAlmaDestinations() {
        let origin = AlmaClient.officialBaseURL
        let unapproved = [
            "http://alma.uni-tuebingen.de/alma",
            "https://example.invalid/alma",
            "https://alma.uni-tuebingen.de:8443/alma",
            "https://user@alma.uni-tuebingen.de/alma"
        ]

        for destination in unapproved {
            let url = URL(string: destination)!
            XCTAssertFalse(AlmaRedirectGuard.matches(url, origin: origin), destination)
        }
    }
}
