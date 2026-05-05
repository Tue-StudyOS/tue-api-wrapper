import SwiftUI
import UIKit

struct TodayPortalMessagesCard: View {
    var model: AppModel

    @State private var phase: PortalMessagesPhase = .idle

    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    Label("Mitteilungen", systemImage: "bell.badge")
                        .font(.headline)
                    Spacer()
                    if case .loading = phase {
                        ProgressView()
                            .controlSize(.small)
                    }
                }

                content
            }
        }
        .task(id: refreshID) {
            await loadIfNeeded()
        }
    }

    private var refreshID: String {
        "\(model.hasCredentials)-\(model.timetableRefreshedAt?.timeIntervalSince1970 ?? 0)"
    }

    @ViewBuilder
    private var content: some View {
        switch phase {
        case .idle, .loading:
            Text("Loading Alma Mitteilungen.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        case .unavailable:
            Text("Connect your university account to load Alma Mitteilungen.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        case .failed(let message):
            AppInlineStatusLine(text: message, systemImage: "exclamationmark.triangle", tint: .orange)
        case .loaded(let items):
            if items.isEmpty {
                Text("No Alma Mitteilungen returned.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                VStack(spacing: 10) {
                    ForEach(items.prefix(3)) { item in
                        PortalMessageRow(item: item)
                    }
                }
            }
        }
    }

    private func loadIfNeeded() async {
        guard model.hasCredentials else {
            phase = .unavailable
            return
        }
        guard case .loading = phase else {
            await load()
            return
        }
    }

    private func load() async {
        phase = .loading
        do {
            guard let credentials = try model.keychain.load() else {
                phase = .unavailable
                return
            }
            guard let baseURL = URL(string: model.baseURLString), baseURL.scheme?.hasPrefix("http") == true else {
                throw AlmaClientError.invalidURL
            }
            let page = try await AlmaClient(baseURL: baseURL).fetchPortalMessages(credentials: credentials)
            phase = .loaded(page.items)
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

private struct PortalMessageRow: View {
    var item: AlmaPortalMessage

    var body: some View {
        Button {
            openURL()
        } label: {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                Image(systemName: item.target == "_blank" ? "doc.text" : "arrow.up.forward.square")
                    .foregroundStyle(Color.accentColor)
                    .frame(width: 22)
                VStack(alignment: .leading, spacing: 3) {
                    Text(item.title)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.primary)
                        .multilineTextAlignment(.leading)
                    if let createdAtLabel = item.createdAtLabel {
                        Text(createdAtLabel)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                Spacer()
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(item.url == nil)
    }

    private func openURL() {
        guard let rawURL = item.url, let url = URL(string: rawURL) else {
            return
        }
        UIApplication.shared.open(url)
    }
}

private enum PortalMessagesPhase: Equatable {
    case idle
    case loading
    case unavailable
    case loaded([AlmaPortalMessage])
    case failed(String)
}
