import SwiftUI

struct StudentCourseLinks: View {
    static let storageKey = "studentConfirmedIliasCourseLinks"
    let almaURL: URL
    let sourceCourse: URL?
    let candidates: [IliasAssignmentDeadline]

    @AppStorage(Self.storageKey) private var savedData = Data()
    @State private var selection: IliasAssignmentDeadline?

    private var links: [String: String] {
        (try? JSONDecoder().decode([String: String].self, from: savedData)) ?? [:]
    }

    private var linkedURL: URL? {
        links[almaURL.absoluteString].flatMap(URL.init(string:))
    }

    private var availableCourses: [IliasAssignmentDeadline] {
        let linked = Set(links.values)
        var seen = Set<String>()
        return candidates.filter {
            guard let url = URL(string: $0.courseURL), url.scheme == "https",
                  url.host == "ovidius.uni-tuebingen.de", !linked.contains($0.courseURL) else { return false }
            return seen.insert($0.courseURL).inserted
        }
    }

    var body: some View {
        if let linkedURL {
            Section("Confirmed ILIAS connection") {
                Link("Open linked course materials", destination: linkedURL)
                Button("Undo course link", role: .destructive) { updateLink(to: nil) }
            }
        } else if sourceCourse == nil, !availableCourses.isEmpty {
            Section("Connect an ILIAS course") {
                ForEach(availableCourses) { candidate in
                    Button(candidate.courseTitle) { selection = candidate }
                }
            }
            .confirmationDialog("Link this ILIAS course?", isPresented: showsConfirmation, titleVisibility: .visible) {
                if let selection {
                    Button("Link courses") { updateLink(to: selection.courseURL) }
                }
            } message: {
                Text("\(selection?.courseTitle ?? "") will appear alongside this Alma course on this device.")
            }
        }
    }

    private var showsConfirmation: Binding<Bool> {
        Binding(get: { selection != nil }, set: { if !$0 { selection = nil } })
    }

    private func updateLink(to destination: String?) {
        var next = links
        next[almaURL.absoluteString] = destination
        if let data = try? JSONEncoder().encode(next) { savedData = data }
    }
}
