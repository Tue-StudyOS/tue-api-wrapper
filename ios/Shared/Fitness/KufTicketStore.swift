import Foundation

struct KufTicketStore {
    private static let defaultKey = "fitness.kuf.tickets.v2"
    private static let legacySingleTicketKey = "fitness.kuf.ticket.v1"

    private let defaults: UserDefaults
    private let key: String
    private let legacyKey: String

    init?() {
        guard let defaults = UserDefaults(suiteName: AppGroup.identifier) else {
            return nil
        }
        self.init(defaults: defaults)
    }

    init(
        defaults: UserDefaults,
        key: String = Self.defaultKey,
        legacyKey: String = Self.legacySingleTicketKey
    ) {
        self.defaults = defaults
        self.key = key
        self.legacyKey = legacyKey
    }

    func loadTicket() -> KufTicket? {
        loadTickets().first
    }

    func loadTickets() -> [KufTicket] {
        guard let data = defaults.data(forKey: key) else {
            return loadLegacyTicket().map { [$0] } ?? []
        }
        if let tickets = try? decoder.decode([KufTicket].self, from: data) {
            return tickets
        }
        return loadLegacyTicket().map { [$0] } ?? []
    }

    func save(_ ticket: KufTicket) throws {
        var tickets = loadTickets()
        if let index = tickets.firstIndex(where: { $0.id == ticket.id }) {
            tickets.remove(at: index)
        }
        tickets.insert(ticket, at: 0)
        try saveTickets(tickets)
    }

    func deleteTicket(_ ticket: KufTicket) throws {
        try saveTickets(loadTickets().filter { $0.id != ticket.id })
    }

    func deleteTicket() {
        defaults.removeObject(forKey: key)
        defaults.removeObject(forKey: legacyKey)
    }

    private func saveTickets(_ tickets: [KufTicket]) throws {
        let data = try encoder.encode(tickets)
        defaults.set(data, forKey: key)
        defaults.removeObject(forKey: legacyKey)
    }

    private func loadLegacyTicket() -> KufTicket? {
        guard let data = defaults.data(forKey: legacyKey) else { return nil }
        return try? decoder.decode(KufTicket.self, from: data)
    }

    private var encoder: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }

    private var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}
