import Foundation
import XCTest
@testable import TueAPI

final class BackendFeedbackClientTests: XCTestCase {
    override func setUp() {
        super.setUp()
        StubURLProtocol.requestHandler = nil
    }

    func testSubmitAppFeedbackPostsStructuredJSON() async throws {
        let expectedRequest = AppFeedbackIssueRequest(
            category: .feature,
            title: "Add offline reminders",
            summary: "Lecture reminders should survive temporary backend outages.",
            area: "Settings",
            expectedBehavior: "Existing reminders remain visible after a failed refresh.",
            reproductionSteps: "1. Enable reminders.\n2. Disconnect the network.\n3. Refresh.",
            appVersion: "0.1.0",
            buildNumber: "1",
            systemVersion: "iOS 17.5",
            deviceModel: "iPhone"
        )

        let responseData = """
        {"issueNumber":42,"issueURL":"https://github.com/SebastianBoehler/tue-api-wrapper/issues/42","title":"[iOS Feedback] Feature: Add offline reminders"}
        """.data(using: .utf8)!

        var capturedRequest: URLRequest?
        StubURLProtocol.requestHandler = { request in
            capturedRequest = request
            return (
                HTTPURLResponse(
                    url: request.url!,
                    statusCode: 201,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!,
                responseData
            )
        }

        let client = try XCTUnwrap(
            BackendClient(
                baseURLString: "https://example.com",
                session: makeStubSession()
            )
        )

        let response = try await client.submitAppFeedback(expectedRequest)

        XCTAssertEqual(response.issueNumber, 42)
        XCTAssertEqual(response.issueURL, "https://github.com/SebastianBoehler/tue-api-wrapper/issues/42")

        let request = try XCTUnwrap(capturedRequest)
        XCTAssertEqual(request.url?.absoluteString, "https://example.com/api/feedback/issues")
        XCTAssertEqual(request.httpMethod, "POST")
        XCTAssertEqual(request.value(forHTTPHeaderField: "Content-Type"), "application/json")
        XCTAssertEqual(
            try JSONDecoder().decode(AppFeedbackIssueRequest.self, from: try XCTUnwrap(requestBody(from: request))),
            expectedRequest
        )
    }

    func testFetchAppFeedbackStatusReadsConfigurationState() async throws {
        let responseData = """
        {"enabled":true,"repository":"SebastianBoehler/tue-api-wrapper","detail":"GitHub feedback issue creation is enabled."}
        """.data(using: .utf8)!

        var capturedRequest: URLRequest?
        StubURLProtocol.requestHandler = { request in
            capturedRequest = request
            return (
                HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!,
                responseData
            )
        }

        let client = try XCTUnwrap(
            BackendClient(
                baseURLString: "https://example.com",
                session: makeStubSession()
            )
        )

        let status = try await client.fetchAppFeedbackStatus()

        XCTAssertEqual(status.enabled, true)
        XCTAssertEqual(status.repository, "SebastianBoehler/tue-api-wrapper")
        XCTAssertEqual(capturedRequest?.url?.absoluteString, "https://example.com/api/feedback/status")
        XCTAssertEqual(capturedRequest?.httpMethod, "GET")
    }

    func testSubmitAppFeedbackSurfacesBackendErrorDetail() async throws {
        StubURLProtocol.requestHandler = { request in
            let body = #"{"detail":"GitHub issue creation failed: HTTP 502: upstream timeout"}"#.data(using: .utf8)!
            return (
                HTTPURLResponse(
                    url: request.url!,
                    statusCode: 502,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!,
                body
            )
        }

        let client = try XCTUnwrap(
            BackendClient(
                baseURLString: "https://example.com",
                session: makeStubSession()
            )
        )

        do {
            _ = try await client.submitAppFeedback(
                AppFeedbackIssueRequest(
                    category: .bug,
                    title: "Settings crash",
                    summary: "Opening feedback crashes on iPad.",
                    area: "Settings",
                    expectedBehavior: nil,
                    reproductionSteps: nil,
                    appVersion: "0.1.0",
                    buildNumber: "1",
                    systemVersion: "iOS 17.5",
                    deviceModel: "iPad"
                )
            )
            XCTFail("Expected backend request to fail.")
        } catch let error as BackendClientError {
            XCTAssertEqual(
                error.localizedDescription,
                "Backend returned HTTP 502: GitHub issue creation failed: HTTP 502: upstream timeout"
            )
        }
    }

    private func makeStubSession() -> URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubURLProtocol.self]
        return URLSession(configuration: configuration)
    }
}

private func requestBody(from request: URLRequest) -> Data? {
    if let body = request.httpBody {
        return body
    }

    guard let stream = request.httpBodyStream else {
        return nil
    }

    stream.open()
    defer { stream.close() }

    let bufferSize = 1024
    var data = Data()
    let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: bufferSize)
    defer { buffer.deallocate() }

    while true {
        let readCount = stream.read(buffer, maxLength: bufferSize)
        if readCount < 0 {
            return nil
        }
        if readCount == 0 {
            break
        }
        data.append(buffer, count: readCount)
    }

    return data
}

private final class StubURLProtocol: URLProtocol {
    static var requestHandler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    override class func canInit(with request: URLRequest) -> Bool {
        request.url?.host == "example.com"
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        request
    }

    override func startLoading() {
        guard let handler = Self.requestHandler else {
            client?.urlProtocol(self, didFailWithError: URLError(.badServerResponse))
            return
        }

        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}
