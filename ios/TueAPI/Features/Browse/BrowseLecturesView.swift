import SwiftUI

struct BrowseLecturesView: View {
    var model: AppModel
    var navigationTitle = "Browse"
    var showsStatus = true

    @State private var selectedDate = Date()
    @State private var query = ""

    var body: some View {
        List {
            StudentListHeading(title: navigationTitle, detail: "Find classes on a specific day.")
            Section("Search day") {
                DatePicker("Date", selection: $selectedDate, displayedComponents: .date)
                Button {
                    Task { await model.browseCurrentLectures(on: selectedDate) }
                } label: {
                    Label("Load Alma lectures", systemImage: "magnifyingglass")
                }
                .disabled(model.browsePhase == .loading)
            }

            if showsStatus {
                Section {
                    browseStatus
                }
            }

            Section("Lectures") {
                if model.browseLectures.isEmpty {
                    ContentUnavailableView(
                        "No lectures loaded",
                        systemImage: "list.bullet.rectangle",
                        description: Text("Choose a date and load Alma's current lectures.")
                    )
                } else if filteredLectures.isEmpty {
                    ContentUnavailableView.search(text: query)
                } else {
                    ForEach(filteredLectures) { lecture in
                        NavigationLink(value: lecture) {
                            AlmaCurrentLectureRow(lecture: lecture)
                        }
                    }
                }
            }
        }
        .navigationTitle(navigationTitle)
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(for: AlmaCurrentLecture.self) { lecture in
            CourseDetailView(lecture: lecture, model: model)
        }
        .searchable(text: $query, prompt: "Filter title, room, lecturer")
        .refreshable {
            await model.browseCurrentLectures(on: selectedDate)
        }
    }

    private var filteredLectures: [AlmaCurrentLecture] {
        let needle = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !needle.isEmpty else { return model.browseLectures }
        return model.browseLectures.filter { lecture in
            lecture.searchText.localizedCaseInsensitiveContains(needle)
        }
    }

    @ViewBuilder
    private var browseStatus: some View {
        switch model.browsePhase {
        case .idle:
            StatusBanner(
                title: "Ready",
                message: idleMessage,
                systemImage: "network"
            )
        case .loading:
            ProgressView("Loading Alma lectures")
        case .loaded(let date, let count, let scope):
            StatusBanner(
                title: "\(count) lectures",
                message: loadedMessage(date: date, scope: scope),
                systemImage: loadedSystemImage(scope: scope)
            )
        case .failed(let message):
            StatusBanner(title: "Browse failed", message: message, systemImage: "exclamationmark.triangle")
        }
    }

    private var idleMessage: String {
        if model.hasCredentials {
            return "Load Alma lectures with public and authenticated results when Alma exposes both."
        }
        return "Load public Alma lectures. Connect your university account in Settings to include signed-in results."
    }

    private func loadedMessage(date: String?, scope: BrowseResultScope) -> String {
        let dateText = date.map { " for \($0)" } ?? ""
        switch scope {
        case .publicOnly:
            return "Alma returned public results\(dateText)."
        case .publicAndAuthenticated(let count):
            if count == 0 {
                return "Signed-in browse ran\(dateText); no additional rows were found."
            }
            let label = count == 1 ? "1 sign-in-only row" : "\(count) sign-in-only rows"
            return "Merged public and authenticated Alma results\(dateText), including \(label)."
        case .publicOnlyAuthenticatedFailed(let message):
            return "Public results loaded\(dateText). Signed-in browse failed: \(message)"
        }
    }

    private func loadedSystemImage(scope: BrowseResultScope) -> String {
        switch scope {
        case .publicOnlyAuthenticatedFailed:
            "exclamationmark.triangle"
        default:
            "checkmark.circle"
        }
    }
}

private struct AlmaCurrentLectureRow: View {
    var lecture: AlmaCurrentLecture

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(lecture.title)
                .font(.headline)
            if let timeRange = lecture.timeRange {
                Text(timeRange)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            if let lecturer = lecture.lecturer ?? lecture.responsibleLecturer {
                Label(lecturer, systemImage: "person")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            if let location = lecture.location {
                Label(location, systemImage: "mappin.and.ellipse")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            footer
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private var footer: some View {
        HStack(spacing: 12) {
            if let eventType = lecture.eventType {
                Text(eventType)
            }
            if let semester = lecture.semester {
                Text(semester)
            }
            if lecture.detailURL != nil {
                Text("Alma detail")
            }
        }
        .font(.caption)
        .foregroundStyle(.secondary)

        if let remark = lecture.remark {
            Text(remark)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

private extension AlmaCurrentLecture {
    var searchText: String {
        [
            title,
            start,
            end,
            number,
            parallelGroup,
            eventType,
            responsibleLecturer,
            lecturer,
            building,
            room,
            semester,
            remark
        ]
        .compactMap { $0?.nilIfEmpty }
        .joined(separator: " ")
    }
}

private extension String {
    var nilIfEmpty: String? {
        isEmpty ? nil : self
    }
}
