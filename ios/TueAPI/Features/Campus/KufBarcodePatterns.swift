enum KufBarcodePatterns {
    static let code39: [Character: String] = [
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

    static let interleaved2of5: [Character: String] = [
        "0": "nnwwn", "1": "wnnnw", "2": "nwnnw", "3": "wwnnn",
        "4": "nnwnw", "5": "wnwnn", "6": "nwwnn", "7": "nnnww",
        "8": "wnnwn", "9": "nwnwn"
    ]

    static let ean13Parity: [Character: String] = [
        "0": "LLLLLL", "1": "LLGLGG", "2": "LLGGLG", "3": "LLGGGL",
        "4": "LGLLGG", "5": "LGGLLG", "6": "LGGGLL", "7": "LGLGLG",
        "8": "LGLGGL", "9": "LGGLGL"
    ]

    static let ean13Left: [Character: String] = [
        "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
        "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
        "8": "0110111", "9": "0001011"
    ]

    static let ean13LeftOdd: [Character: String] = [
        "0": "0100111", "1": "0110011", "2": "0011011", "3": "0100001",
        "4": "0011101", "5": "0111001", "6": "0000101", "7": "0010001",
        "8": "0001001", "9": "0010111"
    ]

    static let ean13Right: [Character: String] = [
        "0": "1110010", "1": "1100110", "2": "1101100", "3": "1000010",
        "4": "1011100", "5": "1001110", "6": "1010000", "7": "1000100",
        "8": "1001000", "9": "1110100"
    ]
}
