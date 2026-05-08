import SwiftUI

struct CareerView: View {
    var model: AppModel

    @Environment(\.openURL) private var openURL
    @State private var phase: CareerLoadPhase = .idle
    @State private var filters: CareerSearchFilters?
    @State private var response: CareerSearchResponse?
    @State private var request = CareerSearchRequest()

    var body: some View {
        List {
            Section("Search") {
                TextField("Internship, thesis, working student", text: $request.query)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .submitLabel(.search)
                    .onSubmit {
                        Task { await search(resetPage: true) }
                    }

                AppFilterMenuButton(
                    title: "Project type",
                    anyLabel: "Any project type",
                    options: filters?.projectTypes ?? [],
                    selection: $request.projectTypeId,
                    optionLabel: \.label,
                    optionValue: \.id,
                    isLoading: phase.isLoading,
                    onSelectionChanged: { _ in submitFilterSearch() }
                )

                AppFilterMenuButton(
                    title: "Subtype",
                    anyLabel: "Any subtype",
                    options: filters?.projectSubtypes ?? [],
                    selection: $request.projectSubtypeId,
                    optionLabel: \.label,
                    optionValue: \.id,
                    isLoading: phase.isLoading,
                    onSelectionChanged: { _ in submitFilterSearch() }
                )

                AppFilterMenuButton(
                    title: "Industry",
                    anyLabel: "Any industry",
                    options: filters?.industries ?? [],
                    selection: $request.industryId,
                    optionLabel: \.label,
                    optionValue: \.id,
                    isLoading: phase.isLoading,
                    onSelectionChanged: { _ in submitFilterSearch() }
                )

                AppFilterMenuButton(
                    title: "Town",
                    anyLabel: "Any town",
                    options: filters?.postalCodes ?? [],
                    selection: $request.postalCode,
                    optionLabel: \.label,
                    optionValue: \.code,
                    isLoading: phase.isLoading,
                    onSelectionChanged: { _ in submitFilterSearch() }
                )

                AppSearchActionRow(
                    searchTitle: "Search",
                    isSearching: phase.isLoading,
                    isSearchDisabled: phase.isLoading,
                    isResetDisabled: phase.isLoading || (!hasActiveFiltersOrQuery && request.page == 0),
                    onSearch: { Task { await search(resetPage: true) } },
                    onReset: resetSearch
                )

                CareerSubscribeButton(model: model, request: request, isDisabled: phase.isLoading || !hasActiveFiltersOrQuery)
            }

            resultsSection
        }
        .navigationTitle("Career")
        .navigationDestination(for: CareerProjectSelection.self) { selection in
            CareerProjectDetailView(model: model, selection: selection)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refreshAll() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(phase.isLoading)
            }
        }
        .task {
            if response == nil {
                await refreshAll()
            }
        }
        .refreshable {
            await refreshAll()
        }
    }

    @ViewBuilder
    private var phaseErrorContent: some View {
        switch phase {
        case .unavailable:
            StatusBanner(
                title: "Backend unavailable",
                message: "The bundled backend URL is not available in this build.",
                systemImage: "exclamationmark.triangle"
            )
        case .failed(let message):
            StatusBanner(title: "Career unavailable", message: message, systemImage: "exclamationmark.triangle")
        default:
            EmptyView()
        }
    }

    @ViewBuilder
    private var resultsSection: some View {
        Section("Open roles") {
            phaseErrorContent

            if phase == .loading && response == nil {
                ForEach(0..<5, id: \.self) { _ in
                    CareerSkeletonRow()
                }
                .redacted(reason: .placeholder)
            } else if let response, response.items.isEmpty {
                ContentUnavailableView.search(text: request.query)
            } else if let response {
                if let url = URL(string: response.sourceURL) {
                    Button {
                        openURL(url)
                    } label: {
                        Label("Open Praxisportal", systemImage: "arrow.up.forward.square")
                    }
                }

                ForEach(response.items) { item in
                    NavigationLink(value: CareerProjectSelection(id: item.id, title: item.title)) {
                        CareerProjectRow(project: item)
                    }
                }

                paginationControls(response)
            } else if !phaseHasError {
                ContentUnavailableView(
                    "No listings loaded",
                    systemImage: "briefcase",
                    description: Text("Refresh to load the newest internships, jobs, thesis topics, and working-student roles.")
                )
            }
        }
    }

    private var phaseHasError: Bool {
        switch phase {
        case .unavailable, .failed:
            true
        default:
            false
        }
    }

    private var hasActiveFiltersOrQuery: Bool {
        !request.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            || request.projectTypeId != nil
            || request.projectSubtypeId != nil
            || request.industryId != nil
            || request.postalCode != nil
    }

    @ViewBuilder
    private func paginationControls(_ response: CareerSearchResponse) -> some View {
        if response.totalPages > 1 {
            HStack {
                Button {
                    Task { await goToPage(response.page - 1) }
                } label: {
                    Label("Previous", systemImage: "chevron.left")
                }
                .disabled(response.page <= 0 || phase.isLoading)

                Spacer()

                Text("\(response.page + 1) / \(response.totalPages)")
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                Spacer()

                Button {
                    Task { await goToPage(response.page + 1) }
                } label: {
                    Label("Next", systemImage: "chevron.right")
                }
                .disabled(response.page + 1 >= response.totalPages || phase.isLoading)
            }
            .id(response.page)
        }
    }

    private func refreshAll() async {
        guard let client = BackendClient(baseURLString: model.portalAPIBaseURLString) else {
            phase = .unavailable
            return
        }

        phase = .loading
        do {
            async let filtersFetch = client.fetchCareerFilters()
            async let searchFetch = client.searchCareerProjects(
                query: request.query,
                projectTypeId: request.projectTypeId,
                projectSubtypeId: request.projectSubtypeId,
                industryId: request.industryId,
                postalCode: request.postalCode ?? "",
                page: request.page,
                perPage: request.perPage
            )
            let (fetchedFilters, fetchedResponse) = try await (filtersFetch, searchFetch)
            filters = fetchedFilters
            applySearchResponse(fetchedResponse)
            phase = .loaded(Date())
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func search(resetPage: Bool) async {
        if resetPage {
            request.resetPage()
        }
        guard let client = BackendClient(baseURLString: model.portalAPIBaseURLString) else {
            phase = .unavailable
            return
        }

        phase = .loading
        do {
            let fetchedResponse = try await client.searchCareerProjects(
                query: request.query,
                projectTypeId: request.projectTypeId,
                projectSubtypeId: request.projectSubtypeId,
                industryId: request.industryId,
                postalCode: request.postalCode ?? "",
                page: request.page,
                perPage: request.perPage
            )
            applySearchResponse(fetchedResponse)
            phase = .loaded(Date())
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func goToPage(_ page: Int) async {
        request.page = max(page, 0)
        await search(resetPage: false)
    }

    private func applySearchResponse(_ fetchedResponse: CareerSearchResponse) {
        filters = fetchedResponse.filters
        response = fetchedResponse
        request.page = fetchedResponse.page
        request.perPage = fetchedResponse.perPage
    }

    private func submitFilterSearch() {
        guard filters != nil, !phase.isLoading else { return }
        Task { await search(resetPage: true) }
    }

    private func resetSearch() {
        request = CareerSearchRequest()
        Task { await search(resetPage: true) }
    }
}

private struct CareerSkeletonRow: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Project type")
                .font(.caption)
            Text("Career listing title")
                .font(.headline)
            Text("Organization · Location")
                .font(.subheadline)
            Text("Preview of the role description")
                .font(.footnote)
        }
        .padding(.vertical, 4)
    }
}
