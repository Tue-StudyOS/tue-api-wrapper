enum KufBarcodeRenderFormat: Equatable {
    case qr
    case aztec
    case pdf417
    case ean13
    case code39
    case interleaved2of5
    case code128
}

extension KufBarcodeRenderer {
    static func renderFormat(for symbology: String) -> KufBarcodeRenderFormat {
        let normalized = symbology
            .replacingOccurrences(of: "-", with: "")
            .lowercased()

        if normalized.contains("qrcode") || normalized.contains("qr") {
            return .qr
        }
        if normalized.contains("aztec") {
            return .aztec
        }
        if normalized.contains("pdf417") {
            return .pdf417
        }
        if normalized.contains("ean13") {
            return .ean13
        }
        if normalized.contains("code39") {
            return .code39
        }
        if normalized.contains("interleaved2of5") || normalized.contains("itf14") {
            return .interleaved2of5
        }
        return .code128
    }
}
