import XCTest
@testable import TueAPI

final class KufBarcodeRendererTests: XCTestCase {
    func testRenderFormatRecognizesTwoDimensionalTicketFormats() {
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.iso.QRCode"), .qr)
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.iso.Aztec"), .aztec)
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.iso.PDF417"), .pdf417)
    }

    func testRendersAValidLinearBarcodeInItsScannedFormat() {
        XCTAssertEqual(KufBarcodeRenderer.renderFormat(for: "org.gs1.EAN-13"), .ean13)
        let image = KufBarcodeRenderer.image(for: "4006381333931", symbology: "org.gs1.EAN-13")
        XCTAssertGreaterThan(image?.size.width ?? 0, image?.size.height ?? 0)
        XCTAssertNil(KufBarcodeRenderer.image(for: "4006381333932", symbology: "org.gs1.EAN-13"))
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
