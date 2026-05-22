import Foundation

struct DeutschlandTicket: Codable, Equatable {
    var barcodeValue: String
    var symbology: String
    var displayName: String?
    var scannedAt: Date

    var formattedCode: String {
        guard barcodeValue.range(of: #"^[A-Za-z0-9]+$"#, options: .regularExpression) != nil else {
            return barcodeValue
        }
        return barcodeValue.chunkedForDeutschlandTicket(every: 4).joined(separator: " ")
    }
}

private extension String {
    func chunkedForDeutschlandTicket(every length: Int) -> [String] {
        guard length > 0 else { return [self] }
        var chunks: [String] = []
        var index = startIndex

        while index < endIndex {
            let next = self.index(index, offsetBy: length, limitedBy: endIndex) ?? endIndex
            chunks.append(String(self[index..<next]))
            index = next
        }

        return chunks
    }
}
