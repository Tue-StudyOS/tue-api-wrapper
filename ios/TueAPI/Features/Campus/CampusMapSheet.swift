import SwiftUI

enum CampusMapSection: String, CaseIterable, Identifiable {
    case places
    case happenings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .places: "Places"
        case .happenings: "Happenings"
        }
    }
}

struct CampusMapStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}

struct CampusMapBottomSheet: View {
    @Binding var selectedSection: CampusMapSection
    var statusLine: CampusMapStatusLine?
    var store: CampusHappeningStore
    var focusLandmark: (CampusLandmark) -> Void
    var focusHappening: (CampusHappening) -> Void
    var openPost: () -> Void

    var body: some View {
        AppSurfaceCard {
            HStack(alignment: .firstTextBaseline) {
                Text("Campus")
                    .font(.title3.weight(.semibold))
                Spacer()
                Button(action: openPost) {
                    Label("Post", systemImage: "plus")
                        .font(.subheadline.weight(.semibold))
                }
                .buttonStyle(.plain)
            }

            Picker("Section", selection: $selectedSection) {
                ForEach(CampusMapSection.allCases) { section in
                    Text(section.title).tag(section)
                }
            }
            .pickerStyle(.segmented)

            if let statusLine {
                AppInlineStatusLine(
                    text: statusLine.text,
                    systemImage: statusLine.systemImage,
                    tint: statusLine.tint,
                    isLoading: statusLine.isLoading
                )
            }

            switch selectedSection {
            case .places:
                CampusPlacesScroller(focusLandmark: focusLandmark)
            case .happenings:
                CampusHappeningsList(
                    happenings: Array(store.happenings.prefix(3)),
                    focusHappening: focusHappening,
                    openPost: openPost
                )
            }
        }
    }
}

struct CampusMapFloatingControls: View {
    var focusUser: () -> Void
    var openPost: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            Button(action: focusUser) {
                Image(systemName: "location.fill")
            }
            Button(action: openPost) {
                Image(systemName: "plus")
            }
        }
        .font(.headline)
        .foregroundStyle(.primary)
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(.thinMaterial, in: Capsule())
    }
}

private struct CampusPlacesScroller: View {
    var focusLandmark: (CampusLandmark) -> Void

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(CampusLandmark.important) { landmark in
                    Button {
                        focusLandmark(landmark)
                    } label: {
                        VStack(alignment: .leading, spacing: 10) {
                            Label(landmark.name, systemImage: landmark.symbolName)
                                .font(.subheadline.weight(.semibold))
                            Text(landmark.detail)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.leading)
                        }
                        .frame(width: 188, alignment: .leading)
                    .padding(14)
                        .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

private struct CampusHappeningsList: View {
    var happenings: [CampusHappening]
    var focusHappening: (CampusHappening) -> Void
    var openPost: () -> Void

    var body: some View {
        if happenings.isEmpty {
            VStack(alignment: .leading, spacing: 10) {
                Text("No student posts yet.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Button("Post the first happening", action: openPost)
                    .font(.subheadline.weight(.semibold))
            }
        } else {
            VStack(spacing: 10) {
                ForEach(happenings) { happening in
                    Button {
                        focusHappening(happening)
                    } label: {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack(alignment: .firstTextBaseline) {
                                Label(happening.title, systemImage: happening.category.symbolName)
                                    .font(.headline)
                                    .foregroundStyle(.primary)
                                Spacer()
                                Text(happening.category.label)
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(happening.category.tint)
                            }
                            Label(happening.locationName, systemImage: "mappin.and.ellipse")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            if let note = happening.note {
                                Text(note)
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)
                            }
                            Text(happening.startsAt.formatted(date: .abbreviated, time: .shortened))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(14)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

struct PostHappeningSheet: View {
    var store: CampusHappeningStore

    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var locationName = ""
    @State private var note = ""
    @State private var category: HappeningCategory = .social
    @State private var startsAt = Date()

    var body: some View {
        NavigationStack {
            Form {
                StudentListHeading(title: "Post a happening", detail: "Add a time and place to the campus map.")
                Section("Happening") {
                    TextField("Coffee after lecture", text: $title)
                    Picker("Type", selection: $category) {
                        ForEach(HappeningCategory.allCases) { category in
                            Label(category.label, systemImage: category.symbolName)
                                .tag(category)
                        }
                    }
                    DatePicker("Starts", selection: $startsAt)
                }

                Section("Location") {
                    TextField("Neue Aula, Morgenstelle, room name", text: $locationName)
                    Text("Use a location Maps can find around Tübingen.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Section("Details") {
                    TextField("What should others know?", text: $note, axis: .vertical)
                        .lineLimit(3, reservesSpace: true)
                }

                if case .failed(let message) = store.phase {
                    Section {
                        AppInlineStatusLine(
                            text: message,
                            systemImage: "exclamationmark.triangle",
                            tint: .orange
                        )
                    }
                }
            }
            .navigationTitle("Post")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Post") {
                        Task {
                            await store.post(
                                title: title,
                                locationName: locationName,
                                note: note,
                                category: category,
                                startsAt: startsAt
                            )
                            if case .saved = store.phase {
                                dismiss()
                            }
                        }
                    }
                    .disabled(store.phase == .saving)
                }
            }
        }
    }
}
