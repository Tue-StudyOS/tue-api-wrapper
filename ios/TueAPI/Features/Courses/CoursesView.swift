import SwiftUI

struct CoursesView: View {
    var model: AppModel
    @AppStorage(StudentCourseLinks.storageKey) private var linksData = Data()

    private var almaCourses: [LectureEvent] {
        var listed = Set<URL>()
        return model.events.sorted { lhs, rhs in
            if lhs.isCancelled != rhs.isCancelled { return !lhs.isCancelled }
            return lhs.startDate < rhs.startDate
        }.filter { event in
            guard let url = event.detailURL else { return true }
            return listed.insert(url).inserted
        }
    }

    private var sourceCourses: [IliasAssignmentDeadline] {
        let manual = (try? JSONDecoder().decode([String: String].self, from: linksData)) ?? [:]
        let linked = Set(almaCourses.compactMap { event in
            CourseDetailReference(event: event).iliasURL
                ?? event.detailURL.flatMap { manual[$0.absoluteString] }.flatMap(URL.init(string:))
        })
        var seen = Set<URL>()
        return model.iliasAssignments.filter { item in
            guard let url = URL(string: item.courseURL), !linked.contains(url) else { return false }
            return seen.insert(url).inserted
        }
    }

    var body: some View {
        List {
            if model.hasCredentials {
                Section("From your Alma timetable") {
                    if almaCourses.isEmpty {
                        if model.phase == .loading {
                            ProgressView("Checking timetable")
                        } else {
                            Text("No courses are listed in your upcoming timetable.").foregroundStyle(.secondary)
                        }
                    }
                    ForEach(almaCourses) { event in
                        NavigationLink {
                            CourseDetailView(event: event, model: model)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(event.title)
                                Text(event.isCancelled ? "Cancelled · \(event.timeRangeText)" : event.timeRangeText)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                if !sourceCourses.isEmpty {
                    Section("Separate ILIAS courses") {
                        ForEach(sourceCourses) { item in
                            if let url = URL(string: item.courseURL), url.scheme == "https" {
                                NavigationLink(item.courseTitle) {
                                    List {
                                        Link("Open course materials in ILIAS", destination: url)
                                        CourseIliasAssignmentsSection(target: url, credentialsLoader: model.keychain)
                                    }
                                    .navigationTitle(item.courseTitle)
                                }
                            }
                        }
                    }
                }
                if case .failed(let message) = model.phase {
                    Section("Alma timetable") { Text(message).foregroundStyle(.secondary) }
                }
            }

            Section("Study and explore") {
                if model.hasCredentials {
                    NavigationLink("Deadlines and tasks") { StudyTasksView(model: model) }
                }
                NavigationLink("Find courses by programme") {
                    ModuleSearchView(model: model, navigationTitle: "Course catalogue")
                }
                NavigationLink("Lectures by date") {
                    BrowseLecturesView(model: model, navigationTitle: "Lectures by date", showsStatus: true)
                }
            }
        }
        .navigationTitle("Courses")
    }
}
