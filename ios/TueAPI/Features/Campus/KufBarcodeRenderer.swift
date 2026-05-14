import CoreImage.CIFilterBuiltins
import SwiftUI

enum KufBarcodeRenderer {
    static func image(for ticket: KufTicket) -> UIImage? {
        if ticket.symbology.localizedCaseInsensitiveContains("QR") {
            return qrImage(for: ticket.barcodeValue)
        }
        if ticket.symbology.localizedCaseInsensitiveContains("EAN-13")
            || ticket.symbology.localizedCaseInsensitiveContains("EAN13") {
            return ean13Image(for: ticket.barcodeValue)
        }
        if ticket.symbology.contains("Code39") {
            return code39Image(for: ticket.barcodeValue)
        }
        if ticket.symbology.contains("Interleaved2of5") || ticket.symbology.contains("ITF14") {
            return interleaved2of5Image(for: ticket.barcodeValue)
        }
        return code128Image(for: ticket.barcodeValue)
    }

    private static func ean13Image(for value: String) -> UIImage? {
        let digits = value.filter(\.isNumber)
        guard digits.count == value.count else { return nil }

        let payload: String
        if digits.count == 12 {
            payload = digits + ean13CheckDigit(for: digits)
        } else if digits.count == 13 {
            let checkDigit = digits.last.map(String.init)
            guard ean13CheckDigit(for: String(digits.prefix(12))) == checkDigit else {
                return nil
            }
            payload = digits
        } else {
            return nil
        }

        guard let firstDigit = payload.first,
              let parity = ean13Parity[firstDigit] else {
            return nil
        }

        let leftDigits = Array(payload.dropFirst().prefix(6))
        let rightDigits = Array(payload.dropFirst(7))
        var modules = "101"

        for (index, digit) in leftDigits.enumerated() {
            let parityIndex = parity.index(parity.startIndex, offsetBy: index)
            let patternSet = parity[parityIndex]
            let patterns = patternSet == "L" ? ean13LeftPatterns : ean13LeftOddPatterns
            guard let pattern = patterns[digit] else { return nil }
            modules += pattern
        }

        modules += "01010"

        for digit in rightDigits {
            guard let pattern = ean13RightPatterns[digit] else { return nil }
            modules += pattern
        }

        modules += "101"
        return moduleImage(from: modules)
    }

    private static func code128Image(for value: String) -> UIImage? {
        guard let data = value.data(using: .ascii) else { return nil }

        let filter = CIFilter.code128BarcodeGenerator()
        filter.message = data
        filter.quietSpace = 24

        return image(from: filter.outputImage, scale: 4)
    }

    private static func qrImage(for value: String) -> UIImage? {
        guard let data = value.data(using: .utf8) else { return nil }

        let filter = CIFilter.qrCodeGenerator()
        filter.message = data
        filter.correctionLevel = "M"

        return image(from: filter.outputImage, scale: 8)
    }

    private static func image(from outputImage: CIImage?, scale: CGFloat) -> UIImage? {
        guard let outputImage else { return nil }
        let scaledImage = outputImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
        guard let cgImage = context.createCGImage(scaledImage, from: scaledImage.extent) else {
            return nil
        }

        return UIImage(cgImage: cgImage)
    }

    private static func code39Image(for value: String) -> UIImage? {
        let encodedValue = "*\(value.uppercased())*"
        guard encodedValue.allSatisfy({ code39Patterns[$0] != nil }) else { return nil }

        let narrowWidth = Metrics.narrowWidth
        let wideWidth = Metrics.wideWidth
        let height = Metrics.height
        let quietZone = Metrics.quietZone
        let characterGap = narrowWidth
        var width = quietZone * 2

        for character in encodedValue {
            width += code39Patterns[character]?.reduce(0) { partial, element in
                partial + (element == "w" ? wideWidth : narrowWidth)
            } ?? 0
            width += characterGap
        }

        let renderer = UIGraphicsImageRenderer(size: CGSize(width: width, height: height))
        return renderer.image { context in
            UIColor.white.setFill()
            context.cgContext.fill(CGRect(x: 0, y: 0, width: width, height: height))
            UIColor.black.setFill()

            var cursor = quietZone
            for character in encodedValue {
                guard let pattern = code39Patterns[character] else { return }
                for (index, element) in pattern.enumerated() {
                    let elementWidth = element == "w" ? wideWidth : narrowWidth
                    if index.isMultiple(of: 2) {
                        context.cgContext.fill(CGRect(x: cursor, y: 0, width: elementWidth, height: height))
                    }
                    cursor += elementWidth
                }
                cursor += characterGap
            }
        }
    }

    private static func interleaved2of5Image(for value: String) -> UIImage? {
        let digits = value.filter(\.isNumber)
        guard digits.count == value.count, !digits.isEmpty else { return nil }
        let encodedDigits = digits.count.isMultiple(of: 2) ? digits : "0\(digits)"
        var pairs: [(Character, Character)] = []
        var index = encodedDigits.startIndex
        while index < encodedDigits.endIndex {
            let next = encodedDigits.index(after: index)
            pairs.append((encodedDigits[index], encodedDigits[next]))
            index = encodedDigits.index(after: next)
        }

        let narrowWidth = Metrics.narrowWidth
        let wideWidth = Metrics.wideWidth
        let height = Metrics.height
        let quietZone = Metrics.quietZone
        var modules: [(isBar: Bool, width: Int)] = [
            (true, narrowWidth),
            (false, narrowWidth),
            (true, narrowWidth),
            (false, narrowWidth)
        ]

        for pair in pairs {
            guard let barPattern = interleaved2of5Patterns[pair.0],
                  let spacePattern = interleaved2of5Patterns[pair.1] else {
                return nil
            }
            for offset in 0..<5 {
                modules.append((true, width(for: barPattern[offset], narrowWidth: narrowWidth, wideWidth: wideWidth)))
                modules.append((false, width(for: spacePattern[offset], narrowWidth: narrowWidth, wideWidth: wideWidth)))
            }
        }

        modules.append(contentsOf: [
            (true, wideWidth),
            (false, narrowWidth),
            (true, narrowWidth)
        ])

        let width = quietZone * 2 + modules.reduce(0) { $0 + $1.width }
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: width, height: height))
        return renderer.image { context in
            UIColor.white.setFill()
            context.cgContext.fill(CGRect(x: 0, y: 0, width: width, height: height))
            UIColor.black.setFill()

            var cursor = quietZone
            for module in modules {
                if module.isBar {
                    context.cgContext.fill(CGRect(x: cursor, y: 0, width: module.width, height: height))
                }
                cursor += module.width
            }
        }
    }

    private static func width(
        for marker: Character,
        narrowWidth: Int,
        wideWidth: Int
    ) -> Int {
        marker == "w" ? wideWidth : narrowWidth
    }

    private static func moduleImage(from modules: String) -> UIImage {
        let moduleWidth = Metrics.moduleWidth
        let width = Metrics.quietZone * 2 + modules.count * moduleWidth
        let height = Metrics.height
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: width, height: height))
        return renderer.image { context in
            UIColor.white.setFill()
            context.cgContext.fill(CGRect(x: 0, y: 0, width: width, height: height))
            UIColor.black.setFill()

            var cursor = Metrics.quietZone
            for module in modules {
                if module == "1" {
                    context.cgContext.fill(CGRect(x: cursor, y: 0, width: moduleWidth, height: height))
                }
                cursor += moduleWidth
            }
        }
    }

    private static func ean13CheckDigit(for first12: String) -> String {
        let sum = first12.enumerated().reduce(0) { partial, item in
            let digit = item.element.wholeNumberValue ?? 0
            return partial + digit * (item.offset.isMultiple(of: 2) ? 1 : 3)
        }
        return String((10 - sum % 10) % 10)
    }

    private static let context = CIContext()

    private enum Metrics {
        static let moduleWidth = 3
        static let narrowWidth = 3
        static let wideWidth = 9
        static let height = 112
        static let quietZone = 24
    }

    private static let code39Patterns: [Character: String] = [
        "0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw",
        "3": "wnwwnnnnn", "4": "nnnwwnnnw", "5": "wnnwwnnnn",
        "6": "nnwwwnnnn", "7": "nnnwnnwnw", "8": "wnnwnnwnn",
        "9": "nnwwnnwnn", "A": "wnnnnwnnw", "B": "nnwnnwnnw",
        "C": "wnwnnwnnn", "D": "nnnnwwnnw", "E": "wnnnwwnnn",
        "F": "nnwnwwnnn", "G": "nnnnnwwnw", "H": "wnnnnwwnn",
        "I": "nnwnnwwnn", "J": "nnnnwwwnn", "K": "wnnnnnnww",
        "L": "nnwnnnnww", "M": "wnwnnnnwn", "N": "nnnnwnnww",
        "O": "wnnnwnnwn", "P": "nnwnwnnwn", "Q": "nnnnnnwww",
        "R": "wnnnnnwwn", "S": "nnwnnnwwn", "T": "nnnnwnwwn",
        "U": "wwnnnnnnw", "V": "nwwnnnnnw", "W": "wwwnnnnnn",
        "X": "nwnnwnnnw", "Y": "wwnnwnnnn", "Z": "nwwnwnnnn",
        "-": "nwnnnnwnw", ".": "wwnnnnwnn", " ": "nwwnnnwnn",
        "$": "nwnwnwnnn", "/": "nwnwnnnwn", "+": "nwnnnwnwn",
        "%": "nnnwnwnwn", "*": "nwnnwnwnn"
    ]

    private static let interleaved2of5Patterns: [Character: String] = [
        "0": "nnwwn", "1": "wnnnw", "2": "nwnnw", "3": "wwnnn",
        "4": "nnwnw", "5": "wnwnn", "6": "nwwnn", "7": "nnnww",
        "8": "wnnwn", "9": "nwnwn"
    ]

    private static let ean13Parity: [Character: String] = [
        "0": "LLLLLL", "1": "LLGLGG", "2": "LLGGLG", "3": "LLGGGL",
        "4": "LGLLGG", "5": "LGGLLG", "6": "LGGGLL", "7": "LGLGLG",
        "8": "LGLGGL", "9": "LGGLGL"
    ]

    private static let ean13LeftPatterns: [Character: String] = [
        "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
        "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
        "8": "0110111", "9": "0001011"
    ]

    private static let ean13LeftOddPatterns: [Character: String] = [
        "0": "0100111", "1": "0110011", "2": "0011011", "3": "0100001",
        "4": "0011101", "5": "0111001", "6": "0000101", "7": "0010001",
        "8": "0001001", "9": "0010111"
    ]

    private static let ean13RightPatterns: [Character: String] = [
        "0": "1110010", "1": "1100110", "2": "1101100", "3": "1000010",
        "4": "1011100", "5": "1001110", "6": "1010000", "7": "1000100",
        "8": "1001000", "9": "1110100"
    ]
}

private extension String {
    subscript(offset: Int) -> Character {
        self[index(startIndex, offsetBy: offset)]
    }
}
