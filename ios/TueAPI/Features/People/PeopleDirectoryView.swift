import SwiftUI

struct PeopleDirectoryView: View {
    @State private var query = ""
    @State private var response: UniversityDirectorySearchResponse?
    @State private var phase: PeopleDirectoryPhase = .idle
    @FocusState private var isQueryFocused: Bool

    private let client = UniversityDirectoryClient()

    var body: some View {
        List {
            StudentListHeading(title: "University directory", detail: "Find people, chairs and departments.")
            Section("Search") {
                TextField("Name or institution", text: $query)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .submitLabel(.search)
                    .focused($isQueryFocused)
                    .onSubmit(submitSearch)

                Text("Uses the public EPV directory. Search for a person, chair, institute, or department.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                AppSearchActionRow(
                    searchTitle: "Search",
                    isSearching: phase.isLoading,
                    isSearchDisabled: !canSearch,
                    isResetDisabled: phase.isLoading || (response == nil && query.isEmpty),
                    onSearch: submitSearch,
                    onReset: resetSearch
                )
            }

            switch phase {
            case .failed(let message):
                Section {
                    StatusBanner(
                        title: "Directory unavailable",
                        message: message,
                        systemImage: "exclamationmark.triangle"
                    )
                }
            case .loading where response == nil:
                Section {
                    ProgressView("Searching the public university directory")
                }
            default:
                if let response {
                    UniversityDirectoryResponseSections(response: response, client: client)
                } else {
                    Section {
                        ContentUnavailableView(
                            "No search yet",
                            systemImage: "person.text.rectangle",
                            description: Text("Enter at least two characters to search the public university directory.")
                        )
                    }
                }
            }
        }
        .navigationTitle("People")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refreshCurrentSearch() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(!canRefresh)
            }
        }
        .refreshable {
            await refreshCurrentSearch()
        }
    }

    private var trimmedQuery: String {
        query.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canSearch: Bool {
        trimmedQuery.count >= 2 && !phase.isLoading
    }

    private var canRefresh: Bool {
        !phase.isLoading && ((response?.query.trimmedOrNil) != nil || trimmedQuery.count >= 2)
    }

    private func submitSearch() {
        guard canSearch else { return }
        isQueryFocused = false
        Task { await search(query: trimmedQuery) }
    }

    private func refreshCurrentSearch() async {
        let current = response?.query.trimmedOrNil ?? trimmedQuery
        guard current.count >= 2 else { return }
        await search(query: current)
    }

    private func search(query: String) async {
        phase = .loading
        do {
            response = try await client.search(query)
            self.query = query
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func resetSearch() {
        query = ""
        response = nil
        phase = .idle
    }
}

private enum PeopleDirectoryPhase: Equatable {
    case idle
    case loading
    case loaded
    case failed(String)

    var isLoading: Bool {
        self == .loading
    }
}
