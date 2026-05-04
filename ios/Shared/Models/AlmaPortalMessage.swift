import Foundation

struct AlmaPortalMessage: Codable, Identifiable, Hashable {
    var id: String
    var title: String
    var url: String?
    var target: String?
    var iconURL: String?
    var createdAtLabel: String?
}

struct AlmaPortalMessagesPage {
    var pageURL: URL
    var items: [AlmaPortalMessage]
}

struct AlmaPortalMessagesListContract {
    var pageURL: URL
    var actionURL: URL
    var formID: String
    var payload: [String: String]
    var toggleTriggerName: String?
    var partialRenderIDs: [String]
}
