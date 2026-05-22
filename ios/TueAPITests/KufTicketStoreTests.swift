import XCTest
@testable import TueAPI

final class KufTicketStoreTests: XCTestCase {
    func testSaveLoadAndDeleteTicket() throws {
        let (store, suiteName) = try makeStore()
        defer { UserDefaults().removePersistentDomain(forName: suiteName) }

        let ticket = KufTicket(
            barcodeValue: "70054028",
            symbology: "org.iso.Code128",
            displayName: "Test Student",
            scannedAt: Date(timeIntervalSince1970: 1_777_777_777)
        )

        try store.save(ticket)
        XCTAssertEqual(store.loadTicket(), ticket)
        XCTAssertEqual(store.loadTickets(), [ticket])

        store.deleteTicket()
        XCTAssertNil(store.loadTicket())
        XCTAssertEqual(store.loadTickets(), [])
    }

    func testSaveKeepsMultipleTicketsAndReplacesMatchingTicket() throws {
        let (store, suiteName) = try makeStore()
        defer { UserDefaults().removePersistentDomain(forName: suiteName) }

        let first = KufTicket(
            barcodeValue: "70054028",
            symbology: "org.iso.Code128",
            displayName: "First",
            scannedAt: Date(timeIntervalSince1970: 1)
        )
        let second = KufTicket(
            barcodeValue: "https://buchung.hsp.uni-tuebingen.de/ticket/abc",
            symbology: "org.iso.QRCode",
            displayName: "Second",
            scannedAt: Date(timeIntervalSince1970: 2)
        )
        let replacement = KufTicket(
            barcodeValue: first.barcodeValue,
            symbology: first.symbology,
            displayName: "Updated",
            scannedAt: Date(timeIntervalSince1970: 3)
        )

        try store.save(first)
        try store.save(second)
        try store.save(replacement)

        XCTAssertEqual(store.loadTickets(), [replacement, second])

        try store.deleteTicket(replacement)
        XCTAssertEqual(store.loadTickets(), [second])
    }

    func testLoadTicketsMigratesLegacySingleTicket() throws {
        let suiteName = "KufTicketStoreTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { UserDefaults().removePersistentDomain(forName: suiteName) }
        let ticket = KufTicket(
            barcodeValue: "70054028",
            symbology: "org.iso.Code128",
            displayName: "Legacy",
            scannedAt: Date(timeIntervalSince1970: 4)
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        defaults.set(try encoder.encode(ticket), forKey: "legacy-ticket")

        let store = KufTicketStore(
            defaults: defaults,
            key: "ticket-list",
            legacyKey: "legacy-ticket"
        )

        XCTAssertEqual(store.loadTickets(), [ticket])
        try store.save(ticket)
        XCTAssertNil(defaults.data(forKey: "legacy-ticket"))
    }

    func testFormattedCodeGroupsBarcodePayload() {
        let ticket = KufTicket(
            barcodeValue: "70054028",
            symbology: "org.iso.Code128",
            displayName: nil,
            scannedAt: .now
        )

        XCTAssertEqual(ticket.formattedCode, "7005 4028")
    }

    func testFormattedCodeKeepsPunctuation() {
        let ticket = KufTicket(
            barcodeValue: "70054-028",
            symbology: "org.iso.Code128",
            displayName: nil,
            scannedAt: .now
        )

        XCTAssertEqual(ticket.formattedCode, "70054-028")
    }

    private func makeStore() throws -> (KufTicketStore, String) {
        let suiteName = "KufTicketStoreTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        return (KufTicketStore(defaults: defaults), suiteName)
    }
}
