import SwiftUI

struct AppRootView: View {
    var model: AppModel
    @AppStorage("exploreWithoutAccount") private var exploreWithoutAccount = false

    @State private var finishingSetup = false
    @State private var selectedTab: StudentTab
    @State private var presentedLink: AppLink?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    init(model: AppModel) {
        self.model = model
        _selectedTab = State(initialValue: model.hasCredentials ? .today : .campus)
    }

    var body: some View {
        Group {
            if !finishingSetup && (model.hasCredentials || exploreWithoutAccount) {
                AppView(model: model, selectedTab: $selectedTab)
            } else {
                NavigationStack {
                    OnboardingView(model: model, exploreWithoutAccount: $exploreWithoutAccount, finishingSetup: $finishingSetup)
                }
            }
        }
        .onChange(of: finishingSetup) { wasFinishing, isFinishing in
            if wasFinishing && !isFinishing && model.hasCredentials { selectedTab = .today }
        }
        .onOpenURL { url in
            guard let link = AppLink(url: url) else { return }
            switch link {
            case .schedule:
                presentedLink = nil
                selectedTab = .schedule
                if !model.hasCredentials { exploreWithoutAccount = true }
            case .kufPass, .kufTrends:
                presentedLink = link
            }
        }
        .sheet(item: $presentedLink) { link in
            NavigationStack {
                switch link {
                case .kufPass:
                    KufTicketView(model: model, onClose: { presentedLink = nil })
                case .kufTrends:
                    KufOccupancyHistoryView()
                        .toolbar {
                            ToolbarItem(placement: .cancellationAction) {
                                Button("Done") { presentedLink = nil }
                            }
                        }
                case .schedule:
                    EmptyView()
                }
            }
        }
        .animation(reduceMotion ? nil : .snappy(duration: 0.28), value: model.hasCredentials)
    }
}
