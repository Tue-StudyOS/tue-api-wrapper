import ActivityKit
import Foundation

enum LiveActivityError: LocalizedError {
    case unavailable

    var errorDescription: String? {
        "Live Activities are not enabled on this device."
    }
}

enum LiveActivityController {
    static func start(for event: LectureEvent) throws {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            throw LiveActivityError.unavailable
        }

        let showsDetails = LectureWidgetPrivacy.showsDetails
        let attributes = LectureActivityAttributes(eventID: event.id)
        let state = LectureActivityAttributes.ContentState(
            title: showsDetails ? event.title : "Lecture",
            startDate: event.startDate,
            endDate: event.endDate,
            location: showsDetails ? event.location : nil
        )
        let content = ActivityContent(state: state, staleDate: event.endDate)
        _ = try Activity<LectureActivityAttributes>.request(attributes: attributes, content: content, pushType: nil)
    }

    static func endAll() async {
        for activity in Activity<LectureActivityAttributes>.activities {
            let content = ActivityContent(state: activity.content.state, staleDate: nil)
            await activity.end(content, dismissalPolicy: .immediate)
        }
    }
}
