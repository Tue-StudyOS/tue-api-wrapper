import XCTest
@testable import TueAPI

final class AppLinkTests: XCTestCase {
    func testKufShortcutCarriesOnlyADestination() {
        let url = AppLink.kufPass.url
        XCTAssertEqual(url.absoluteString, "tueapi://kuf-pass")
        XCTAssertEqual(AppLink(url: url), .kufPass)
    }

    func testOnlyTheRegisteredShortcutOpensThePass() {
        for address in [
            "https://kuf-pass", "tueapi://account", "tueapi://kuf-pass/other",
            "tueapi://kuf-pass?barcode=example", "tueapi://kuf-pass#example",
            "tueapi://other@kuf-pass", "tueapi://kuf-pass:3000"
        ] {
            XCTAssertNil(AppLink(url: URL(string: address)!), address)
        }
    }
}
