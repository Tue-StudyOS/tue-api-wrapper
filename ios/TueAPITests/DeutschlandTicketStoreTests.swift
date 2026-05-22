import XCTest
@testable import TueAPI

final class DeutschlandTicketStoreTests: XCTestCase {
    func testSaveLoadAndDeleteTicket() throws {
        let (store, suiteName) = try makeStore()
        defer { UserDefaults().removePersistentDomain(forName: suiteName) }

        let ticket = DeutschlandTicket(
            barcodeValue: "D-TICKET-LOCAL-TEST",
            symbology: "org.iso.QRCode",
            displayName: "Test Student",
            scannedAt: Date(timeIntervalSince1970: 1_777_777_777)
        )

        try store.save(ticket)
        XCTAssertEqual(store.loadTicket(), ticket)

        store.deleteTicket()
        XCTAssertNil(store.loadTicket())
    }

    func testSaveReplacesExistingTicket() throws {
        let (store, suiteName) = try makeStore()
        defer { UserDefaults().removePersistentDomain(forName: suiteName) }

        let first = DeutschlandTicket(
            barcodeValue: "FIRST",
            symbology: "org.iso.Aztec",
            displayName: "First",
            scannedAt: Date(timeIntervalSince1970: 1)
        )
        let replacement = DeutschlandTicket(
            barcodeValue: "SECOND",
            symbology: "org.iso.PDF417",
            displayName: "Second",
            scannedAt: Date(timeIntervalSince1970: 2)
        )

        try store.save(first)
        try store.save(replacement)

        XCTAssertEqual(store.loadTicket(), replacement)
    }

    private func makeStore() throws -> (DeutschlandTicketStore, String) {
        let suiteName = "DeutschlandTicketStoreTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        return (DeutschlandTicketStore(defaults: defaults), suiteName)
    }
}
