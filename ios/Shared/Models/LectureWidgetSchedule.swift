import Foundation

/// Selects cached lectures and timeline changes without fetching private data.
enum LectureWidgetSchedule {
    static func upcoming(_ events: [LectureEvent], at date: Date) -> [LectureEvent] {
        events
            .filter { !$0.isCancelled && ($0.endDate ?? $0.startDate) >= date }
            .sorted { $0.startDate < $1.startDate }
    }

    static func entryDates(_ events: [LectureEvent], from now: Date, until refresh: Date) -> [Date] {
        let boundaries = Set(events.compactMap { event -> Date? in
            guard !event.isCancelled else { return nil }
            let end = (event.endDate ?? event.startDate).addingTimeInterval(1)
            return end > now && end < refresh ? end : nil
        })
        return [now] + boundaries.sorted()
    }
}
