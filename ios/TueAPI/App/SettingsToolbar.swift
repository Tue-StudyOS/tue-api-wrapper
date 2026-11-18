import SwiftUI

private struct AccountToolbarModifier: ViewModifier {
    var model: AppModel
    var mailBadgeStore: MailBadgeStore

    func body(content: Content) -> some View {
        content
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    NavigationLink {
                        StudentAccountView(model: model, mailBadgeStore: mailBadgeStore)
                    } label: {
                        Label("Account", systemImage: "person.crop.circle")
                    }
                }
            }
    }
}

extension View {
    func accountToolbar(model: AppModel, mailBadgeStore: MailBadgeStore) -> some View {
        modifier(AccountToolbarModifier(model: model, mailBadgeStore: mailBadgeStore))
    }
}
