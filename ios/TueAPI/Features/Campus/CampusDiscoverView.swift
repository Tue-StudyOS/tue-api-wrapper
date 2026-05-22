import SwiftUI

struct CampusDiscoverView: View {
    var model: AppModel

    @State private var selectedSection: CampusDiscoverSection = .map

    var body: some View {
        VStack(spacing: 0) {
            Picker("Campus section", selection: $selectedSection) {
                ForEach(CampusDiscoverSection.allCases) { section in
                    Text(section.title).tag(section)
                }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .padding(.vertical, 10)

            Divider()

            switch selectedSection {
            case .map:
                CampusMapView()
            case .food:
                CampusFoodView(model: model)
            case .seats:
                CampusSeatView()
            case .deutschlandTicket:
                DeutschlandTicketView(model: model)
            case .kufCard:
                KufTicketView(model: model)
            }
        }
    }
}

private enum CampusDiscoverSection: String, CaseIterable, Identifiable {
    case map
    case food
    case seats
    case deutschlandTicket
    case kufCard

    var id: Self { self }

    var title: String {
        switch self {
        case .map:
            "Map"
        case .food:
            "Food"
        case .seats:
            "Seats"
        case .deutschlandTicket:
            "D-Ticket"
        case .kufCard:
            "KuF"
        }
    }
}
