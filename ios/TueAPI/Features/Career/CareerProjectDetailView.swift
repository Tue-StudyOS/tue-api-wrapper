import SwiftUI

struct CareerProjectDetailView: View {
    var model: AppModel
    var selection: CareerProjectSelection

    @Environment(\.openURL) private var openURL
    @State private var phase: CareerDetailPhase = .loading
    @State private var detail: CareerProjectDetail?

    var body: some View {
        List {
            StudentListHeading(title: selection.title)
            content
        }
        .navigationTitle("Listing")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await load()
        }
        .refreshable {
            await load()
        }
    }

    @ViewBuilder
    private var content: some View {
        switch phase {
        case .loading:
            ProgressView("Loading listing")
        case .failed(let message):
            StatusBanner(title: "Listing unavailable", message: message, systemImage: "exclamationmark.triangle")
        case .loaded:
            if let detail {
                summarySection(detail)
                organizationsSection(detail)
                textSection("Description", detail.description)
                textSection("Requirements", detail.requirements)
                originalListingSection(detail)
            }
        }
    }

    private func summarySection(_ detail: CareerProjectDetail) -> some View {
        Section("Listing") {
            Text(detail.title)
                .font(.headline)
            if let location = detail.location?.trimmedOrNil {
                Label(location, systemImage: "mappin.and.ellipse")
            }
            if let start = CareerDateFormatter.displayText(detail.startDate) {
                Label("Start \(start)", systemImage: "calendar")
            }
            if let listed = CareerDateFormatter.displayText(detail.createdAt) {
                Label("Listed \(listed)", systemImage: "clock")
            }
            tagList("Project types", detail.projectTypes)
            tagList("Industries", detail.industries)
        }
    }

    @ViewBuilder
    private func organizationsSection(_ detail: CareerProjectDetail) -> some View {
        if !detail.organizations.isEmpty {
            Section("Organizations") {
                ForEach(detail.organizations) { organization in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(organization.name)
                            .font(.subheadline.weight(.medium))
                        if let logoURL = organization.logoURL?.trimmedOrNil {
                            Text(logoURL)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .textSelection(.enabled)
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func textSection(_ title: String, _ value: String?) -> some View {
        if let text = value?.trimmedOrNil {
            Section(title) {
                Text(text)
                    .font(.body)
                    .textSelection(.enabled)
            }
        }
    }

    @ViewBuilder
    private func originalListingSection(_ detail: CareerProjectDetail) -> some View {
        if let value = detail.sourceURL?.trimmedOrNil, let url = URL(string: value) {
            Section {
                Button {
                    openURL(url)
                } label: {
                    Label("Open original listing", systemImage: "arrow.up.forward.square")
                }
            }
        }
    }

    @ViewBuilder
    private func tagList(_ title: String, _ values: [String]) -> some View {
        if !values.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(values.joined(separator: ", "))
                    .font(.subheadline)
            }
        }
    }

    private func load() async {
        guard let client = BackendClient(baseURLString: model.portalAPIBaseURLString) else {
            phase = .failed("The bundled backend URL is required before opening Praxisportal listings.")
            return
        }

        phase = .loading
        do {
            detail = try await client.fetchCareerProject(id: selection.id)
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}
