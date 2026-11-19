import SwiftUI

struct MailView: View {
    var model: AppModel
    var mailBadgeStore: MailBadgeStore

    private let mailService = OnDeviceMailService()

    @State private var phase: MailLoadPhase = .idle
    @State private var mailboxes: [MailboxSummary] = []
    @State private var inbox: MailInboxSummary?
    @State private var selectedMailbox = "INBOX"
    @State private var searchText = ""
    @State private var unreadOnly = false

    private var topStatusLine: MailStatusLine? {
        if !model.hasCredentials {
            return MailStatusLine(
                text: "Connect your university account in Settings to read mail.",
                systemImage: "lock",
                tint: .secondary
            )
        }
        if case .failed(let message) = phase {
            return MailStatusLine(
                text: message,
                systemImage: "exclamationmark.triangle",
                tint: .orange
            )
        }
        return nil
    }

    private var footerTimestamp: String? {
        guard case .loaded(let date) = phase else { return nil }
        return "Last updated \(date.formatted(date: .abbreviated, time: .shortened))"
    }

    private var approvalHighlight: (message: MailMessageSummary, notice: MailUniversityApprovalNotice)? {
        guard let message = inbox?.messages.first(where: { $0.universityApprovalNotice != nil }),
              let notice = message.universityApprovalNotice else {
            return nil
        }
        return (message, notice)
    }

    private var mailboxOptions: [MailboxSummary] {
        var ordered: [MailboxSummary] = [
            MailboxSummary(
                name: "INBOX",
                label: "Inbox",
                specialUse: nil,
                messageCount: nil,
                unreadCount: inbox?.mailbox == "INBOX" ? inbox?.unreadCount : mailboxes.first(where: { $0.name == "INBOX" })?.unreadCount
            )
        ]
        ordered.append(contentsOf: mailboxes.filter { $0.name != "INBOX" })

        var seen = Set<String>()
        return ordered.filter { mailbox in
            seen.insert(mailbox.label).inserted
        }
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                MailHeader(subtitle: headerSubtitle)

                if let topStatusLine {
                    AppInlineStatusLine(
                        text: topStatusLine.text,
                        systemImage: topStatusLine.systemImage,
                        tint: topStatusLine.tint,
                        isLoading: topStatusLine.isLoading
                    )
                }

                MailFilterSurface(
                    mailboxOptions: mailboxOptions,
                    selectedMailbox: $selectedMailbox,
                    searchText: $searchText,
                    unreadOnly: $unreadOnly,
                    isLoading: phase.isLoading,
                    mailboxTitle: mailboxTitle(_:),
                    applySearch: { Task { await refreshInbox() } }
                )

                if let approvalHighlight {
                    NavigationLink(
                        value: MailMessageSelection(
                            uid: approvalHighlight.message.uid,
                            mailbox: inbox?.mailbox ?? selectedMailbox,
                            subject: approvalHighlight.message.subject
                        )
                    ) {
                        MailApprovalCard(notice: approvalHighlight.notice)
                    }
                    .buttonStyle(.plain)
                }

                messagesContent

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
        .navigationDestination(for: MailMessageSelection.self) { selection in
            MailMessageDetailView(selection: selection)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task { await refreshAll() }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(phase.isLoading)
            }
        }
        .task {
            if inbox == nil {
                await refreshAll()
            }
        }
        .refreshable {
            await refreshAll()
        }
        .onChange(of: selectedMailbox) {
            Task { await refreshInbox() }
        }
        .onChange(of: unreadOnly) {
            Task { await refreshInbox() }
        }
    }

    private var headerSubtitle: String {
        if inbox != nil {
            return "\(unreadText) in \(inboxTitle)"
        }
        return model.hasCredentials ? "Uni Tuebingen mailbox" : "Login required"
    }

    @ViewBuilder
    private var messagesContent: some View {
        if phase == .loading && inbox == nil {
            VStack(spacing: 12) {
                ForEach(0..<5, id: \.self) { _ in
                    MailSkeletonCard()
                }
            }
        } else if let inbox, inbox.messages.isEmpty {
            AppSurfaceCard {
                ContentUnavailableView(
                    "No messages",
                    systemImage: unreadOnly ? "envelope.badge" : "tray",
                    description: Text("Change the mailbox or filters, then refresh.")
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 28)
            }
        } else if let inbox {
            VStack(spacing: 12) {
                ForEach(inbox.messages) { message in
                    NavigationLink(
                        value: MailMessageSelection(
                            uid: message.uid,
                            mailbox: inbox.mailbox,
                            subject: message.subject
                        )
                    ) {
                        MailMessageRow(message: message)
                    }
                    .buttonStyle(.plain)
                }
            }
        } else {
            AppSurfaceCard {
                ContentUnavailableView(
                    "Mail not loaded",
                    systemImage: "envelope",
                    description: Text("Refresh after connecting your university account in Settings.")
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, 28)
            }
        }
    }

    private var inboxTitle: String {
        guard let inbox else { return "Inbox" }
        if let mailbox = mailboxes.first(where: { $0.name == inbox.mailbox }) {
            return mailbox.label
        }
        return inbox.mailbox
    }

    private var unreadText: String {
        guard let inbox else { return "Mail not loaded" }
        return inbox.unreadCount == 1 ? "1 unread message" : "\(inbox.unreadCount) unread messages"
    }

    private func refreshAll() async {
        phase = .loading
        do {
            async let mailboxFetch = mailService.fetchMailboxes()
            async let inboxFetch = mailService.fetchMailInbox(
                mailbox: selectedMailbox,
                query: searchText,
                unreadOnly: unreadOnly
            )
            let (fetchedMailboxes, fetchedInbox) = try await (mailboxFetch, inboxFetch)
            mailboxes = fetchedMailboxes
            inbox = fetchedInbox
            mailBadgeStore.update(from: fetchedMailboxes, fallbackInbox: fetchedInbox)
            phase = .loaded(Date())
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func refreshInbox() async {
        phase = .loading
        do {
            inbox = try await mailService.fetchMailInbox(
                mailbox: selectedMailbox,
                query: searchText,
                unreadOnly: unreadOnly
            )
            if let inbox {
                mailBadgeStore.update(from: inbox)
            }
            phase = .loaded(Date())
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func mailboxTitle(_ mailbox: MailboxSummary) -> String {
        if let unreadCount = mailbox.unreadCount, unreadCount > 0 {
            return "\(mailbox.label) \(unreadCount)"
        }
        return mailbox.label
    }
}
