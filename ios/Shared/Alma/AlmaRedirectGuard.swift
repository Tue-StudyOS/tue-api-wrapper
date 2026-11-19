import Foundation

final class AlmaRedirectGuard: NSObject, URLSessionTaskDelegate {
    private let origin: URL

    init(origin: URL) {
        self.origin = origin
    }

    static func matches(_ url: URL, origin: URL) -> Bool {
        guard let host = origin.host?.lowercased() else { return false }
        return url.scheme?.lowercased() == "https" && origin.scheme?.lowercased() == "https"
            && url.host?.lowercased() == host
            && (url.port ?? 443) == (origin.port ?? 443)
            && url.user == nil && url.password == nil
    }

    func urlSession(
        _ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
        newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void
    ) {
        completionHandler(request.url.map { Self.matches($0, origin: origin) } == true ? request : nil)
    }
}
