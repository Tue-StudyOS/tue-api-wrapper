import Foundation

enum CampusArea: CaseIterable, Identifiable {
    case places, support, opportunities

    var id: Self { self }

    var title: String {
        switch self {
        case .places: "Food, study and transport"
        case .support: "People and support"
        case .opportunities: "Sports, talks and careers"
        }
    }

    var detail: String {
        switch self {
        case .places: "Menus, seats, buildings and tickets"
        case .support: "Contacts, housing and settling in"
        case .opportunities: "Events, recordings and opportunities"
        }
    }

    var symbol: String {
        switch self {
        case .places: "map"
        case .support: "person.2"
        case .opportunities: "figure.run"
        }
    }

    var destinations: [CampusDestination] {
        switch self {
        case .places: [.food, .seats, .map, .transport]
        case .support: [.people, .international, .housing, .city, .documents]
        case .opportunities: [.sports, .occupancy, .talks, .recordings, .career]
        }
    }
}

enum CampusDestination: CaseIterable, Identifiable {
    case kuf, food, seats, map, transport, occupancy, people, talks, career, documents, courses
    case international, housing, city, sports, recordings

    var id: Self { self }

    var title: String { label.0 }
    var detail: String { label.1 }
    var symbol: String { label.2 }

    var searchTerms: String {
        switch self {
        case .kuf: "barcode QR gym fitness Kraft und Fitnesshalle"
        case .documents: "enrollment certificate transcript Alma Immatrikulationsbescheinigung"
        case .courses: "Alma lecture programme module"
        default: ""
        }
    }

    private var label: (String, String, String) {
        switch self {
        case .kuf: ("KuF pass", "Show or scan your entry barcode", "barcode")
        case .food: ("Food and canteens", "Menus and opening hours", "fork.knife")
        case .seats: ("Study spaces", "Available seats", "chair")
        case .map: ("Campus map", "Buildings and directions", "map")
        case .transport: ("Deutschlandticket", "Your saved ticket", "tram")
        case .occupancy: ("KuF activity", "Locally recorded occupancy", "chart.bar")
        case .people: ("University directory", "Find people and departments", "person.2")
        case .talks: ("Talks and events", "Upcoming university events", "mic")
        case .career: ("Career opportunities", "Projects and placements", "briefcase")
        case .documents: ("Documents", "Certificates and official reports", "doc.text")
        case .courses: ("Course catalogue", "Search modules and courses", "books.vertical")
        case .international: ("International student support", "University website", "arrow.up.right")
        case .housing: ("Student housing", "Studierendenwerk website", "arrow.up.right")
        case .city: ("City registration and services", "City of Tübingen website", "arrow.up.right")
        case .sports: ("University sports", "Hochschulsport programme", "arrow.up.right")
        case .recordings: ("Lecture recordings", "TIMMS website", "arrow.up.right")
        }
    }

    var externalURL: URL? {
        let address: String
        switch self {
        case .international:
            address = "https://uni-tuebingen.de/en/international/study-in-tuebingen/"
        case .housing:
            address = "https://www.my-stuwe.de/wohnen/online-bewerbung/"
        case .city:
            address = "https://www.tuebingen.de/verwaltung/onlinedienste"
        case .sports:
            address = "https://uni-tuebingen.de/pt/einrichtungen/zentrale-einrichtungen/hochschulsport/sportprogramm/"
        case .recordings:
            address = "https://timms.uni-tuebingen.de/"
        default:
            return nil
        }
        return URL(string: address)
    }
}
