import ActivityKit
import WidgetKit
import SwiftUI

struct LectureLiveActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: LectureActivityAttributes.self) { context in
            LectureLiveActivityView(state: context.state)
                .widgetURL(AppLink.schedule.url)
                .activitySystemActionForegroundColor(.primary)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Label(context.state.startDate.formatted(date: .omitted, time: .shortened), systemImage: "calendar")
                        .font(.caption2)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    if let endDate = context.state.endDate {
                        Text(endDate, style: .time)
                            .font(.caption2)
                    }
                }
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(LectureWidgetPrivacy.showsDetails ? context.state.title : "Lecture")
                            .font(.subheadline.weight(.semibold))
                            .lineLimit(2)
                        if LectureWidgetPrivacy.showsDetails, let location = context.state.location, !location.isEmpty {
                            Label(location, systemImage: "mappin.and.ellipse")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            } compactLeading: {
                Image(systemName: "calendar")
                    .foregroundStyle(.white)
            } compactTrailing: {
                // Progress ring showing how much of the lecture has elapsed.
                // Falls back to a static time label when no end date is available.
                if let endDate = context.state.endDate {
                    ProgressView(
                        timerInterval: context.state.startDate...endDate,
                        countsDown: false
                    ) {
                        EmptyView()
                    } currentValueLabel: {
                        EmptyView()
                    }
                    .progressViewStyle(.circular)
                    .tint(.white)
                    .frame(width: 20, height: 20)
                } else {
                    Text(context.state.startDate, style: .time)
                        .font(.caption2)
                }
            } minimal: {
                Image(systemName: "calendar")
            }
            .widgetURL(AppLink.schedule.url)
        }
    }
}

struct LectureLiveActivityView: View {
    let state: LectureActivityAttributes.ContentState

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(LectureWidgetPrivacy.showsDetails ? state.title : "Lecture")
                .font(.headline)
                .lineLimit(2)
            Text(timeText)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if LectureWidgetPrivacy.showsDetails, let location = state.location, !location.isEmpty {
                Label(location, systemImage: "mappin.and.ellipse")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
    }

    private var timeText: String {
        let start = state.startDate.formatted(date: .abbreviated, time: .shortened)
        guard let endDate = state.endDate else {
            return start
        }
        return "\(start) - \(endDate.formatted(date: .omitted, time: .shortened))"
    }
}
