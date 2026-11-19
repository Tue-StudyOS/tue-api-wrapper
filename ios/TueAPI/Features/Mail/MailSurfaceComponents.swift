import SwiftUI

struct MailHeader: View {
    let subtitle: String

    var body: some View {
        StudentScreenHeading(title: "University mail", detail: subtitle)
    }
}

struct MailFilterSurface: View {
    let mailboxOptions: [MailboxSummary]
    @Binding var selectedMailbox: String
    @Binding var searchText: String
    @Binding var unreadOnly: Bool
    let isLoading: Bool
    let mailboxTitle: (MailboxSummary) -> String
    let applySearch: () -> Void

    var body: some View {
        AppSurfaceCard {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(mailboxOptions) { mailbox in
                        Button {
                            selectedMailbox = mailbox.name
                        } label: {
                            Text(mailboxTitle(mailbox))
                                .font(.subheadline.weight(.semibold))
                                .padding(.horizontal, 12)
                                .padding(.vertical, 9)
                                .background(
                                    mailbox.name == selectedMailbox ? Color.studentActionFill : Color(uiColor: .secondarySystemBackground),
                                    in: Capsule()
                                )
                                .foregroundStyle(mailbox.name == selectedMailbox ? Color.white : .primary)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

            HStack(spacing: 12) {
                HStack(spacing: 10) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Search subject, sender, preview", text: $searchText)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .submitLabel(.search)
                        .onSubmit {
                            applySearch()
                        }
                    if !searchText.isEmpty {
                        Button {
                            searchText = ""
                            applySearch()
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

                Button {
                    unreadOnly.toggle()
                } label: {
                    Label("Unread", systemImage: unreadOnly ? "line.3.horizontal.decrease.circle.fill" : "line.3.horizontal.decrease.circle")
                        .font(.subheadline.weight(.semibold))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 11)
                        .background(unreadOnly ? Color.accentColor.opacity(0.12) : Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .buttonStyle(.plain)
            }

            if isLoading {
                AppInlineStatusLine(text: "Refreshing mailbox.", tint: .accentColor, isLoading: true)
            }
        }
    }
}

struct MailApprovalCard: View {
    let notice: MailUniversityApprovalNotice

    var body: some View {
        AppSurfaceCard {
            Text("University action")
                .font(.caption.weight(.semibold))
                .foregroundStyle(Color.accentColor)
                .textCase(.uppercase)
            Text(notice.title)
                .font(.headline)
            Text(notice.message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }
}

struct MailSkeletonCard: View {
    var body: some View {
        MailMessageRow(
            message: MailMessageSummary(
                uid: UUID().uuidString,
                subject: "Subject preview",
                fromName: "Sender",
                fromAddress: nil,
                receivedAt: nil,
                preview: "Preview text for the message.",
                universityApprovalNotice: nil,
                isUnread: false
            )
        )
        .redacted(reason: .placeholder)
    }
}

struct MailStatusLine {
    var text: String
    var systemImage: String?
    var tint: Color
    var isLoading = false
}
