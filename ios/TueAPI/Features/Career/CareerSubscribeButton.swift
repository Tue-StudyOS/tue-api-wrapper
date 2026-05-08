import SwiftUI

struct CareerSubscribeButton: View {
    var model: AppModel
    var request: CareerSearchRequest
    var isDisabled: Bool

    @State private var message: String?
    @State private var isLoading = false

    var body: some View {
        Button {
            Task { await subscribe() }
        } label: {
            Label(isLoading ? "Subscribing" : "Subscribe to filters", systemImage: "bell.badge")
        }
        .disabled(isLoading || isDisabled)

        if let message {
            Text(message)
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }

    private func subscribe() async {
        guard let credentials = try? model.keychain.load() else {
            message = "Save university credentials before subscribing to Praxisportal filters."
            return
        }
        isLoading = true
        defer { isLoading = false }
        do {
            let subscription = try await PraxisportalOnDeviceClient(credentials: credentials)
                .createSubscription(query: subscriptionQuery)
            message = "Subscription \(subscription.id) is active."
        } catch {
            message = error.localizedDescription
        }
    }

    private var subscriptionQuery: CareerSubscriptionQuery {
        CareerSubscriptionQuery(
            text: request.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? [] : [request.query],
            industries: request.industryId.map { [String($0)] } ?? [],
            projectSubtypes: request.projectSubtypeId.map { [String($0)] } ?? [],
            postalCode: request.postalCode.map { [$0] } ?? [],
            projectTypeId: request.projectTypeId.map { [String($0)] } ?? []
        )
    }
}
