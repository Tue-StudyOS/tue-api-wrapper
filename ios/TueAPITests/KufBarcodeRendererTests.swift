import XCTest
@testable import TueAPI

final class KufBarcodeRendererTests: XCTestCase {
    func testRenderFormatRecognizesTwoDimensionalTicketFormats() {
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.iso.QRCode"), .qr)
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.iso.Aztec"), .aztec)
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.iso.PDF417"), .pdf417)
    }

    func testRendersTwoDimensionalTicketFormats() {
        let samples: [(String, String)] = [
            ("org.iso.QRCode", "STUDYOS-QR-TEST"),
            ("org.iso.Aztec", "STUDYOS-AZTEC-TEST"),
            ("org.iso.PDF417", "STUDYOS-PDF417-TEST")
        ]

        for (symbology, payload) in samples {
            let image = KufBarcodeRenderer.image(for: payload, symbology: symbology)

            XCTAssertNotNil(image, "Expected \(symbology) to render.")
            XCTAssertGreaterThan(image?.size.width ?? 0, 0)
            XCTAssertGreaterThan(image?.size.height ?? 0, 0)
        }
    }
}
