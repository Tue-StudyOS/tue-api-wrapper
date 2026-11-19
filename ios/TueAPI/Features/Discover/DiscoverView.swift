import SwiftUI

struct DiscoverView: View {
    var model: AppModel
    @State private var query = ""

    private var searchText: String { query.trimmingCharacters(in: .whitespacesAndNewlines) }

    private var matchingCourses: [LectureEvent] {
        guard model.hasCredentials, !searchText.isEmpty else { return [] }
        var urls = Set<URL>()
        return model.events.filter { event in
            guard event.title.localizedStandardContains(searchText) else { return false }
            guard let url = event.detailURL else { return true }
            return urls.insert(url).inserted
        }
    }

    private var results: [CampusDestination] {
        CampusDestination.allCases.filter { destination in
            [destination.title, destination.detail, destination.searchTerms].contains {
                $0.localizedStandardContains(searchText)
            }
        }
    }

    var body: some View {
        List {
            if searchText.isEmpty {
                Section {
                    destinationLink(.kuf)
                    destinationLink(.seats)
                }
                Section("Explore") {
                    ForEach(CampusArea.allCases) { area in
                        NavigationLink {
                            List {
                                StudentListHeading(title: area.title, detail: area.detail)
                                ForEach(area.destinations) { destinationLink($0) }
                            }
                            .navigationTitle(area.title)
                            .navigationBarTitleDisplayMode(.inline)
                        } label: {
                            CampusServiceRow(title: area.title, detail: area.detail, symbol: area.symbol)
                        }
                    }
                }
            } else if results.isEmpty && matchingCourses.isEmpty {
                ContentUnavailableView.search(text: searchText)
            } else {
                if !matchingCourses.isEmpty {
                    Section("From your timetable") {
                        ForEach(matchingCourses) { event in
                            NavigationLink(event.title) {
                                CourseDetailView(event: event, model: model)
                            }
                        }
                    }
                }
                if !results.isEmpty {
                    Section("Places and services") {
                        ForEach(results) { destinationLink($0) }
                    }
                }
            }
        }
        .navigationTitle("Campus")
        .searchable(text: $query, prompt: "Courses, places and services")
    }

    @ViewBuilder
    private func destinationLink(_ destination: CampusDestination) -> some View {
        if let url = destination.externalURL {
            Link(destination: url) {
                CampusServiceRow(title: destination.title, detail: destination.detail, symbol: "arrow.up.right")
            }
        } else {
            NavigationLink {
                switch destination {
                case .kuf: KufTicketView(model: model)
                case .occupancy: KufOccupancyHistoryView()
                case .map: CampusMapView()
                case .food: CampusFoodView(model: model)
                case .seats: CampusSeatView()
                case .transport: DeutschlandTicketView(model: model)
                case .people: PeopleDirectoryView()
                case .talks: TalksView()
                case .career: CareerView(model: model)
                case .documents: StudentDocumentsView(model: model)
                case .courses: ModuleSearchView(model: model, navigationTitle: "Course catalogue")
                case .international, .housing, .city, .sports, .recordings: EmptyView()
                }
            } label: {
                CampusServiceRow(title: destination.title, detail: destination.detail, symbol: destination.symbol)
            }
        }
    }
}

private struct CampusServiceRow: View {
    let title: String
    let detail: String
    let symbol: String

    var body: some View {
        Label {
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.body.weight(.medium))
                Text(detail).font(.subheadline).foregroundStyle(.secondary)
            }
            .padding(.vertical, 3)
        } icon: {
            Image(systemName: symbol)
                .foregroundStyle(Color.accentColor)
        }
    }
}
