import Foundation

enum AppLink: String {
    case kufPass = "kuf-pass"

    var url: URL { URL(string: "tueapi://\(rawValue)")! }

    init?(url: URL) {
        guard url.scheme?.lowercased() == "tueapi",
              let host = url.host,
              url.path.isEmpty, url.query == nil, url.fragment == nil,
              url.user == nil, url.password == nil, url.port == nil else { return nil }
        self.init(rawValue: host)
    }
}
