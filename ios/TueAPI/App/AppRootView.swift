import SwiftUI

struct AppRootView: View {
    var model: AppModel
    @AppStorage("exploreWithoutAccount") private var exploreWithoutAccount = false

    @State private var finishingSetup = false
    @State private var showsKufPass = false

    var body: some View {
        Group {
            if !finishingSetup && (model.hasCredentials || exploreWithoutAccount) {
                AppView(model: model)
            } else {
                NavigationStack {
                    OnboardingView(model: model, exploreWithoutAccount: $exploreWithoutAccount, finishingSetup: $finishingSetup)
                }
            }
        }
        .onOpenURL { url in
            if AppLink(url: url) == .kufPass {
                showsKufPass = true
            }
        }
        .sheet(isPresented: $showsKufPass) {
            NavigationStack {
                KufTicketView(model: model, onClose: { showsKufPass = false })
            }
        }
        .animation(.snappy(duration: 0.28), value: model.hasCredentials)
    }
}
