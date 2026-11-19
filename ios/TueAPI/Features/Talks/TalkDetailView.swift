import SwiftUI

struct TalkDetailView: View {
    let talk: Talk

    var body: some View {
        List {
            StudentListHeading(title: talk.title)
            Section {
                LabeledContent("Speaker", value: talk.speakerName ?? "Speaker pending")
                if let date = talk.startDate {
                    LabeledContent("Time", value: TalksDateParser.formattedDate(date))
                }
                LabeledContent("Location", value: talk.location ?? "Location pending")
            }

            if talk.location?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false {
                Section("Quick navigation") {
                    CampusNavigationActions(talk: talk)
                }
            }

            if !talk.tags.isEmpty {
                Section("Tags") {
                    ForEach(talk.tags) { tag in
                        Text(tag.name)
                    }
                }
            }

            if let bio = talk.speakerBio, !bio.isEmpty {
                Section("Speaker Bio") {
                    Text(bio)
                        .textSelection(.enabled)
                }
            }

            Section("Abstract") {
                Text(talk.description ?? "No abstract provided.")
                    .textSelection(.enabled)
            }

            if let sourceURL = talk.sourceURL {
                Section {
                    Link("Open original talk", destination: sourceURL)
                }
            }
        }
        .navigationTitle("Talk")
        .navigationBarTitleDisplayMode(.inline)
    }
}
