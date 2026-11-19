import SwiftUI

struct CampusFoodView: View {
    var model: AppModel

    @State private var phase: CampusFoodLoadPhase = .idle
    @State private var canteens: [CampusFoodPlanCanteen] = []
    @State private var selectedDate = Date()

    private var visibleCanteens: [CampusFoodPlanCanteen] {
        canteens.filter { !$0.menus.isEmpty }
    }

    private var headerSubtitle: String {
        let dateLabel = selectedDate.formatted(date: .abbreviated, time: .omitted)
        let menuCount = visibleCanteens.reduce(0) { $0 + $1.menus.count }

        if phase.isLoading && canteens.isEmpty {
            return "Loading live my-stuwe menus for \(dateLabel.lowercased())"
        }
        if menuCount > 0 {
            let menuLabel = menuCount == 1 ? "menu" : "menus"
            let canteenLabel = visibleCanteens.count == 1 ? "canteen" : "canteens"
            return "\(menuCount) \(menuLabel) across \(visibleCanteens.count) \(canteenLabel) for \(dateLabel.lowercased())"
        }
        return "Live my-stuwe meal plans for Tübingen mensas and cafeterias"
    }

    private var topStatusLine: CampusFoodStatusLine? {
        switch phase {
        case .loading where !canteens.isEmpty:
            return CampusFoodStatusLine(
                text: "Refreshing live my-stuwe menus.",
                tint: .accentColor,
                isLoading: true
            )
        case .unavailable:
            return CampusFoodStatusLine(
                text: "The bundled backend URL is not available in this build.",
                systemImage: "exclamationmark.triangle",
                tint: .orange
            )
        case .failed(let message):
            return CampusFoodStatusLine(
                text: message,
                systemImage: "exclamationmark.triangle",
                tint: .orange
            )
        default:
            return nil
        }
    }

    private var footerTimestamp: String? {
        guard case .loaded(let date, _) = phase else { return nil }
        return "Last updated \(date.formatted(date: .abbreviated, time: .shortened))"
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                CampusFoodHeader(subtitle: headerSubtitle)

                if let topStatusLine {
                    AppInlineStatusLine(
                        text: topStatusLine.text,
                        systemImage: topStatusLine.systemImage,
                        tint: topStatusLine.tint,
                        isLoading: topStatusLine.isLoading
                    )
                }

                CampusFoodControlsCard(
                    selectedDate: $selectedDate,
                    isLoading: phase.isLoading && canteens.isEmpty
                )

                content

                if let footerTimestamp {
                    Text(footerTimestamp)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)
                }
            }
            .padding(16)
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refreshFoodPlan() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(phase.isLoading)
            }
        }
        .refreshable {
            await refreshFoodPlan()
        }
        .task {
            if canteens.isEmpty {
                await refreshFoodPlan()
            }
        }
        .onChange(of: selectedDate) {
            Task { await refreshFoodPlan() }
        }
    }

    @ViewBuilder
    private var content: some View {
        if phase.isLoading && canteens.isEmpty {
            VStack(spacing: 12) {
                ForEach(0..<4, id: \.self) { _ in
                    CampusFoodSkeletonCard()
                }
            }
        } else if visibleCanteens.isEmpty {
            AppSurfaceCard {
                ContentUnavailableView(
                    unavailableTitle,
                    systemImage: unavailableSystemImage,
                    description: Text(unavailableDescription)
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 28)
            }
        } else {
            VStack(spacing: 12) {
                ForEach(visibleCanteens) { canteen in
                    CampusFoodCanteenCard(canteen: canteen)
                }
            }
        }
    }

    private var unavailableTitle: String {
        switch phase {
        case .unavailable:
            "Backend unavailable"
        case .failed:
            "Could not load menus"
        default:
            "No menus published"
        }
    }

    private var unavailableSystemImage: String {
        switch phase {
        case .unavailable, .failed:
            "exclamationmark.triangle"
        default:
            "fork.knife"
        }
    }

    private var unavailableDescription: String {
        switch phase {
        case .unavailable:
            "This build has no valid public backend URL for the campus food feed."
        case .failed(let message):
            message
        default:
            "No Tübingen mensa menus were published for \(selectedDate.formatted(date: .abbreviated, time: .omitted).lowercased())."
        }
    }

    private func refreshFoodPlan() async {
        guard let client = BackendClient(baseURLString: model.portalAPIBaseURLString) else {
            phase = .unavailable
            return
        }

        phase = .loading
        do {
            let fetchedCanteens = try await client.fetchCampusFoodPlan(on: selectedDate)
            canteens = fetchedCanteens
            phase = .loaded(Date(), fetchedCanteens.reduce(0) { $0 + $1.menus.count })
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

private struct CampusFoodStatusLine {
    let text: String
    var systemImage: String? = nil
    var tint: Color = .secondary
    var isLoading = false
}
