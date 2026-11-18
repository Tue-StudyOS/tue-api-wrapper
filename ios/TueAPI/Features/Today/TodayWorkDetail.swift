import SwiftUI

struct TodayWorkDetail: View {
    let item: TodayUrgencyItem

    var body: some View {
        List {
            Section(item.source) {
                LabeledContent("Course", value: item.subtitle)
                LabeledContent("Deadline", value: item.detail)
                if let status = item.status {
                    LabeledContent("Status", value: status)
                }
                if let lastSubmission = item.lastSubmission {
                    LabeledContent("Last submission", value: lastSubmission)
                }
                if let requirement = item.requirement {
                    LabeledContent("Requirement", value: requirement)
                }
            }

            if let url = item.sourceURL {
                Section {
                    Link(destination: url) {
                        Label("Open in \(item.source)", systemImage: "arrow.up.right")
                    }
                }
            }
        }
        .navigationTitle(item.title)
        .navigationBarTitleDisplayMode(.inline)
    }
}
