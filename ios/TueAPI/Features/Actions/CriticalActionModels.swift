import Foundation

enum CriticalActionKind: Hashable {
    case almaCourseRegistration
}

struct CriticalActionIntent: Identifiable, Hashable {
    var id = UUID()
    var kind: CriticalActionKind
    var portal: String
    var title: String
    var actionLabel: String
    var targetURL: URL?
    var endpoint: String
    var method: String
    var sideEffects: [String]
    var requiredInputs: [String]
    var confirmButtonTitle: String
}

enum CriticalActionLoadPhase: Equatable {
    case idle
    case preparing
    case ready
    case submitting
    case unknown
    case completed(String)
    case failed(String)

    var isBusy: Bool {
        switch self {
        case .preparing, .submitting:
            true
        default:
            false
        }
    }
}
