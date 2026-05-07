import Foundation

struct SeatfinderClient {
    private static let apiURL = URL(string: "https://seatfinder.bibliothek.kit.edu/tuebingen/getdata.php")!

    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func fetchAvailability(
        locations: [String] = SeatfinderClient.defaultLocationIDs
    ) async throws -> CampusSeatAvailability {
        let url = try makeURL(locations: locations)
        var request = URLRequest(url: url)
        request.setValue("application/json, text/javascript;q=0.9, */*;q=0.8", forHTTPHeaderField: "Accept")
        request.setValue("tue-api-wrapper-ios/0.1 (+https://seatfinder.bibliothek.kit.edu/)", forHTTPHeaderField: "User-Agent")

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw SeatfinderClientError.server("Seatfinder did not return an HTTP response.")
        }
        guard (200..<300).contains(http.statusCode) else {
            throw SeatfinderClientError.server("Seatfinder request failed with HTTP \(http.statusCode).")
        }
        return try Self.parse(data, sourceURL: http.url ?? url)
    }

    static func parse(_ data: Data, sourceURL: URL, retrievedAt: Date = Date()) throws -> CampusSeatAvailability {
        let payload = try decodePayload(data)
        let estimates = firstMapping(in: payload, key: "seatestimate")
        let locations = firstMapping(in: payload, key: "location")
        let rows = locations.keys.sorted().compactMap { locationID in
            buildLocationStatus(
                locationID: locationID,
                locationRows: locations[locationID] ?? [],
                estimateRows: estimates[locationID] ?? []
            )
        }

        return CampusSeatAvailability(
            sourceURL: sourceURL.absoluteString,
            retrievedAt: ISO8601DateFormatter().string(from: retrievedAt),
            locations: rows
        )
    }

    private func makeURL(locations: [String]) throws -> URL {
        let locationCSV = locations
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: ",")
        guard !locationCSV.isEmpty else {
            throw SeatfinderClientError.invalidLocations
        }

        var components = URLComponents(url: Self.apiURL, resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "location[0]", value: locationCSV),
            URLQueryItem(name: "values[0]", value: "seatestimate,manualcount"),
            URLQueryItem(name: "after[0]", value: "-10800seconds"),
            URLQueryItem(name: "before[0]", value: "now"),
            URLQueryItem(name: "limit[0]", value: "-17"),
            URLQueryItem(name: "location[1]", value: locationCSV),
            URLQueryItem(name: "values[1]", value: "location"),
            URLQueryItem(name: "after[1]", value: ""),
            URLQueryItem(name: "before[1]", value: "now"),
            URLQueryItem(name: "limit[1]", value: "1")
        ]
        guard let url = components?.url else {
            throw SeatfinderClientError.invalidURL
        }
        return url
    }

    private static func decodePayload(_ data: Data) throws -> [Any] {
        let objectData: Data
        if let text = String(data: data, encoding: .utf8),
           let stripped = stripJSONP(text).data(using: .utf8) {
            objectData = stripped
        } else {
            objectData = data
        }
        guard let payload = try JSONSerialization.jsonObject(with: objectData) as? [Any] else {
            throw SeatfinderClientError.parsing("Seatfinder response was not a list.")
        }
        return payload
    }

    private static func stripJSONP(_ text: String) -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let open = trimmed.firstIndex(of: "("), trimmed.hasSuffix(")") || trimmed.hasSuffix(");") else {
            return trimmed
        }
        let close = trimmed.lastIndex(of: ")") ?? trimmed.endIndex
        return String(trimmed[trimmed.index(after: open)..<close])
    }

    private static func firstMapping(in payload: [Any], key: String) -> [String: [[String: Any]]] {
        for item in payload {
            guard let object = item as? [String: Any],
                  let mapping = object[key] as? [String: Any] else {
                continue
            }
            return mapping.reduce(into: [:]) { result, entry in
                result[entry.key] = rows(from: entry.value)
            }
        }
        return [:]
    }

    private static func rows(from value: Any) -> [[String: Any]] {
        (value as? [Any])?.compactMap { $0 as? [String: Any] } ?? []
    }

    private static func buildLocationStatus(
        locationID: String,
        locationRows: [[String: Any]],
        estimateRows: [[String: Any]]
    ) -> CampusSeatLocation? {
        guard let location = latestRow(locationRows) else {
            return nil
        }
        let estimate = latestRow(estimateRows) ?? [:]
        var totalSeats = intValue(location["available_seats"])
        let freeSeats = intValue(estimate["free_seats"])
        let occupiedSeats = intValue(estimate["occupied_seats"])
        if totalSeats == nil, let freeSeats, let occupiedSeats {
            totalSeats = freeSeats + occupiedSeats
        }

        return CampusSeatLocation(
            locationID: locationID,
            name: textValue(location["name"]) ?? locationID,
            longName: textValue(location["long_name"]),
            level: textValue(location["level"]),
            building: textValue(location["building"]),
            room: textValue(location["room"]),
            totalSeats: totalSeats,
            freeSeats: freeSeats,
            occupiedSeats: occupiedSeats,
            occupancyPercent: occupancyPercent(occupiedSeats: occupiedSeats, totalSeats: totalSeats),
            updatedAt: timestampText(estimate["timestamp"] ?? location["timestamp"]),
            url: textValue(location["url"]),
            geoCoordinates: textValue(location["geo_coordinates"])
        )
    }

    private static func latestRow(_ rows: [[String: Any]]) -> [String: Any]? {
        rows.max { left, right in
            (timestampText(left["timestamp"]) ?? "") < (timestampText(right["timestamp"]) ?? "")
        }
    }

    private static func timestampText(_ value: Any?) -> String? {
        if let object = value as? [String: Any], let rawDate = textValue(object["date"]) {
            return Self.seatfinderDateFormatter.date(from: rawDate)
                .map { ISO8601DateFormatter().string(from: $0) } ?? rawDate
        }
        return textValue(value)
    }

    private static func occupancyPercent(occupiedSeats: Int?, totalSeats: Int?) -> Double? {
        guard let occupiedSeats, let totalSeats, totalSeats > 0 else {
            return nil
        }
        return (Double(occupiedSeats) / Double(totalSeats) * 1000).rounded() / 10
    }

    private static func intValue(_ value: Any?) -> Int? {
        if let int = value as? Int {
            return int
        }
        if let double = value as? Double {
            return Int(double)
        }
        if let text = textValue(value) {
            return Int(text)
        }
        return nil
    }

    private static func textValue(_ value: Any?) -> String? {
        guard let value else { return nil }
        let text = "\(value)".trimmingCharacters(in: .whitespacesAndNewlines)
        return text.isEmpty || text == "<null>" ? nil : text
    }

    private static let seatfinderDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Europe/Berlin")
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSSSSS"
        return formatter
    }()

    static let defaultLocationIDs = [
        "UBH1", "UBB2", "UBB2HLS", "UBA3A", "UBA3C", "UBA4A", "UBA4B", "UBA4C",
        "UBA5A", "UBA5B", "UBA5C", "UBA6A", "UBA6B", "UBA6C", "UBCEG", "UBCUG",
        "UBLZN", "UBNEG", "UBWZA", "UBWZB"
    ]
}

enum SeatfinderClientError: LocalizedError {
    case invalidLocations
    case invalidURL
    case server(String)
    case parsing(String)

    var errorDescription: String? {
        switch self {
        case .invalidLocations:
            "At least one seatfinder location id is required."
        case .invalidURL:
            "Could not build the seatfinder request URL."
        case .server(let message), .parsing(let message):
            message
        }
    }
}
