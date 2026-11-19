import SwiftUI

struct TalksView: View {
    @State private var talks: [Talk] = []
    @State private var phase: TalksLoadPhase = .idle
    @State private var scope: TalksScope = .upcoming
    @State private var query = ""

    private let client = TalksClient()

    private var filteredTalks: [Talk] {
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedQuery.isEmpty else { return talks }
        return talks.filter { talk in
            [
                talk.title,
                talk.description ?? "",
                talk.location ?? "",
                talk.speakerName ?? "",
                talk.speakerBio ?? "",
                talk.tags.map(\.name).joined(separator: " ")
            ]
            .joined(separator: "\n")
            .localizedCaseInsensitiveContains(trimmedQuery)
        }
    }

    private var headerSubtitle: String {
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedQuery.isEmpty {
            return "\(filteredTalks.count) matches in \(scope.label.lowercased()) talks"
        }
        if case .loaded(_, let count) = phase {
            let label = count == 1 ? "talk" : "talks"
            return "\(count) \(scope.label.lowercased()) \(label) from the public calendar"
        }
        return "Public AI talks and guest lectures"
    }

    private var isRefreshing: Bool {
        phase == .loading || (phase == .idle && talks.isEmpty)
    }

    private var topStatusLine: TalksStatusLine? {
        guard case .failed(let message) = phase else { return nil }
        return TalksStatusLine(
            text: message,
            systemImage: "exclamationmark.triangle",
            tint: .orange
        )
    }

    private var footerTimestamp: String? {
        guard case .loaded(let date, _) = phase else { return nil }
        return "Last updated \(date.formatted(date: .abbreviated, time: .shortened))"
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                TalksHeader(subtitle: headerSubtitle)

                if let topStatusLine {
                    AppInlineStatusLine(
                        text: topStatusLine.text,
                        systemImage: topStatusLine.systemImage,
                        tint: topStatusLine.tint,
                        isLoading: topStatusLine.isLoading
                    )
                }

                TalksFilterSurface(
                    scope: $scope,
                    query: $query,
                    isLoading: isRefreshing
                )

                talksContent

                if let footerTimestamp {
                    Text(footerTimestamp)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)
                }
            }
            .padding(16)
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refreshTalks() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(isRefreshing)
            }
        }
        .refreshable {
            await refreshTalks()
        }
        .task {
            if talks.isEmpty {
                await refreshTalks()
            }
        }
        .onChange(of: scope) {
            Task { await refreshTalks() }
        }
    }

    @ViewBuilder
    private var talksContent: some View {
        if isRefreshing && talks.isEmpty {
            VStack(spacing: 12) {
                ForEach(0..<4, id: \.self) { _ in
                    TalkSkeletonCard()
                }
            }
        } else if filteredTalks.isEmpty {
            AppSurfaceCard {
                ContentUnavailableView(
                    "No talks",
                    systemImage: "mic.slash",
                    description: Text(query.isEmpty ? "No talks were returned by the public calendar." : "No talks matched this search.")
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 28)
            }
        } else {
            VStack(spacing: 12) {
                ForEach(filteredTalks) { talk in
                    NavigationLink {
                        TalkDetailView(talk: talk)
                    } label: {
                        TalkCard(talk: talk)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func refreshTalks() async {
        phase = .loading
        do {
            let fetchedTalks = try await client.fetchTalks(scope: scope, limit: 100)
            talks = fetchedTalks
            phase = .loaded(Date(), fetchedTalks.count)
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

private struct TalksHeader: View {
    let subtitle: String

    var body: some View {
        StudentScreenHeading(title: "Talks and events", detail: subtitle)
    }
}

private struct TalksFilterSurface: View {
    @Binding var scope: TalksScope
    @Binding var query: String
    let isLoading: Bool

    var body: some View {
        AppSurfaceCard {
            HStack(spacing: 10) {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)

                TextField("Search talks, speaker, location", text: $query)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()

                if !query.isEmpty {
                    Button {
                        query = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 11)
            .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 16, style: .continuous))

            Picker("Range", selection: $scope) {
                ForEach(TalksScope.allCases) { scope in
                    Text(scope.label).tag(scope)
                }
            }
            .pickerStyle(.segmented)

            if isLoading {
                AppInlineStatusLine(text: "Refreshing public talks.", tint: .accentColor, isLoading: true)
            }
        }
    }
}

private struct TalkCard: View {
    let talk: Talk

    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 12) {
                Text(talk.title)
                    .font(.headline)
                    .foregroundStyle(.primary)

                Text(talk.speakerName ?? talk.location ?? "Speaker pending")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                HStack(spacing: 12) {
                    if let date = talk.startDate {
                        Label(TalksDateParser.formattedDate(date), systemImage: "calendar")
                    }
                    if let location = talk.location, !location.isEmpty {
                        Label(location, systemImage: "mappin.and.ellipse")
                    }
                }
                .font(.caption)
                .foregroundStyle(.secondary)

                if let description = talk.description?.trimmingCharacters(in: .whitespacesAndNewlines), !description.isEmpty {
                    Text(description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(3)
                }

                if !talk.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(talk.tags) { tag in
                                Text(tag.name)
                                    .font(.caption.weight(.semibold))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color.accentColor.opacity(0.12), in: Capsule())
                            }
                        }
                    }
                }
            }
        }
    }
}

private struct TalkSkeletonCard: View {
    var body: some View {
        TalkCard(
            talk: Talk(
                id: 0,
                title: "Talk title placeholder",
                timestamp: "2026-01-01T12:00:00",
                description: "Abstract preview placeholder",
                location: "Lecture Hall",
                speakerName: "Speaker",
                speakerBio: nil,
                disabled: false,
                tags: []
            )
        )
        .redacted(reason: .placeholder)
    }
}

private struct TalksStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}
