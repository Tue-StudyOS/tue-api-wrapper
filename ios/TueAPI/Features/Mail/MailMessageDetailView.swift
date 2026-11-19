import SwiftUI

struct MailMessageDetailView: View {
    var selection: MailMessageSelection

    private let mailService = OnDeviceMailService()

    @State private var phase: MailDetailPhase = .loading
    @State private var detail: MailMessageDetail?

    var body: some View {
        List {
            StudentListHeading(title: selection.subject)
            content
        }
        .navigationTitle("Message")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await load()
        }
        .refreshable {
            await load()
        }
    }

    @ViewBuilder
    private var content: some View {
        switch phase {
        case .loading:
            ProgressView("Loading message")
        case .failed(let message):
            StatusBanner(title: "Message unavailable", message: message, systemImage: "exclamationmark.triangle")
        case .loaded:
            if let detail {
                header(detail)
                bodySection(detail)
                attachmentsSection(detail)
            }
        }
    }

    private func header(_ detail: MailMessageDetail) -> some View {
        Section("Message") {
            LabeledContent("From", value: sender(detail))
            if let received = MailDateFormatter.displayText(detail.receivedAt) {
                LabeledContent("Received", value: received)
            }
            if !detail.toRecipients.isEmpty {
                recipients("To", detail.toRecipients)
            }
            if !detail.ccRecipients.isEmpty {
                recipients("Cc", detail.ccRecipients)
            }
            if detail.isUnread {
                Label("Unread", systemImage: "envelope.badge")
                    .foregroundStyle(.blue)
            }
            if let notice = detail.universityApprovalNotice {
                MailUniversityApprovalBadge(notice: notice, showsMessage: true)
            }
        }
    }

    @ViewBuilder
    private func bodySection(_ detail: MailMessageDetail) -> some View {
        Section("Body") {
            if let body = detail.bodyText?.trimmedOrNil {
                Text(body)
                    .font(.body)
                    .textSelection(.enabled)
            } else {
                ContentUnavailableView(
                    "No body text",
                    systemImage: "doc.text",
                    description: Text("The message did not include readable text.")
                )
            }
        }
    }

    @ViewBuilder
    private func attachmentsSection(_ detail: MailMessageDetail) -> some View {
        if !detail.attachmentNames.isEmpty {
            Section("Attachments") {
                ForEach(detail.attachmentNames, id: \.self) { name in
                    Label(name, systemImage: "paperclip")
                }
            }
        }
    }

    private func recipients(_ title: String, _ values: [String]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(values.joined(separator: "\n"))
                .font(.subheadline)
                .textSelection(.enabled)
        }
    }

    private func sender(_ detail: MailMessageDetail) -> String {
        detail.fromName?.trimmedOrNil ?? detail.fromAddress?.trimmedOrNil ?? "Unknown sender"
    }

    private func load() async {
        phase = .loading
        do {
            detail = try await mailService.fetchMailMessage(uid: selection.uid, mailbox: selection.mailbox)
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}
