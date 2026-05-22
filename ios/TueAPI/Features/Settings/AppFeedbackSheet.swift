import SwiftUI

struct AppFeedbackSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var draft = AppFeedbackDraft()
    @State private var phase: AppFeedbackSubmissionPhase = .idle

    private let context = AppFeedbackContext.current
    private let feedbackClient = AppFeedbackGitHubClient()

    var body: some View {
        NavigationStack {
            Form {
                if phase.showsStatusSection {
                    Section {
                        statusSectionContent
                    }
                }

                Section("Privacy") {
                    StatusBanner(
                        title: "Public feedback issue",
                        message: "This creates a GitHub issue from this device. Do not include login details, student IDs, grades, or other personal data.",
                        systemImage: "exclamationmark.shield"
                    )
                }
                if !AppFeedbackGitHubClient.isConfigured {
                    Section {
                        StatusBanner(
                            title: "Feedback unavailable",
                            message: "This build has no GitHub feedback token configured.",
                            systemImage: "exclamationmark.triangle"
                        )
                    }
                }

                Section("Feedback") {
                    Picker("Type", selection: $draft.category) {
                        ForEach(AppFeedbackCategory.allCases) { category in
                            Text(category.title).tag(category)
                        }
                    }
                    .disabled(phase.isSubmitted)

                    TextField("Short title", text: $draft.title)
                        .disabled(phase.isSubmitted)

                    TextField("Where in the app? (optional)", text: $draft.area, axis: .vertical)
                        .lineLimit(1...2)
                        .disabled(phase.isSubmitted)

                    TextField("What happened or what should change?", text: $draft.summary, axis: .vertical)
                        .lineLimit(4...8)
                        .disabled(phase.isSubmitted)

                    TextField("How should it behave instead? (optional)", text: $draft.expectedBehavior, axis: .vertical)
                        .lineLimit(3...6)
                        .disabled(phase.isSubmitted)

                    TextField("How can we reproduce it? (optional)", text: $draft.reproductionSteps, axis: .vertical)
                        .lineLimit(3...6)
                        .disabled(phase.isSubmitted)
                }

                Section {
                    LabeledContent("App version", value: context.versionLabel)
                    LabeledContent("OS", value: context.systemVersion)
                    LabeledContent("Device", value: context.deviceModel)
                } header: {
                    Text("Technical Context")
                } footer: {
                    Text("Your university login details are never attached to feedback.")
                }
            }
            .navigationTitle("Send Feedback")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button(phase.isSubmitted ? "Done" : "Cancel") {
                        dismiss()
                    }
                }

                if !phase.isSubmitted {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button(phase.isSubmitting ? "Creating..." : "Create") {
                            submit()
                        }
                        .disabled(!canSubmit)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var statusSectionContent: some View {
        switch phase {
        case .idle:
            EmptyView()
        case .submitting:
            StatusBanner(
                title: "Creating GitHub issue",
                message: "Submitting feedback to GitHub...",
                systemImage: "arrow.triangle.2.circlepath"
            )
        case .created(let issue):
            VStack(alignment: .leading, spacing: 12) {
                StatusBanner(
                    title: "GitHub issue created",
                    message: issue.title,
                    systemImage: "checkmark.circle"
                )

                Link("Open GitHub issue", destination: issue.issueURL)
            }
        case .failed(let message):
            StatusBanner(
                title: "Feedback failed",
                message: message,
                systemImage: "exclamationmark.triangle"
            )
        }
    }

    private var canSubmit: Bool {
        AppFeedbackGitHubClient.isConfigured
            && !phase.isSubmitting
            && draft.title.trimmedOrNil != nil
            && draft.summary.trimmedOrNil != nil
    }

    private func submit() {
        phase = .submitting
        let request = draft.asRequest(context: context)
        Task {
            do {
                let issue = try await feedbackClient.createIssue(request)
                await MainActor.run {
                    phase = .created(issue)
                }
            } catch {
                await MainActor.run {
                    phase = .failed(error.localizedDescription)
                }
            }
        }
    }
}

private struct AppFeedbackDraft {
    var category: AppFeedbackCategory = .improvement
    var title = ""
    var area = ""
    var summary = ""
    var expectedBehavior = ""
    var reproductionSteps = ""

    func asRequest(context: AppFeedbackContext) -> AppFeedbackIssueRequest {
        AppFeedbackIssueRequest(
            category: category,
            title: title.trimmingCharacters(in: .whitespacesAndNewlines),
            summary: summary.trimmingCharacters(in: .whitespacesAndNewlines),
            area: area.trimmedOrNil,
            expectedBehavior: expectedBehavior.trimmedOrNil,
            reproductionSteps: reproductionSteps.trimmedOrNil,
            appVersion: context.appVersion,
            buildNumber: context.buildNumber,
            systemVersion: context.systemVersion,
            deviceModel: context.deviceModel
        )
    }
}

private enum AppFeedbackSubmissionPhase: Equatable {
    case idle
    case submitting
    case created(AppFeedbackIssue)
    case failed(String)

    var isSubmitted: Bool {
        if case .created = self {
            true
        } else {
            false
        }
    }

    var showsStatusSection: Bool {
        switch self {
        case .idle:
            false
        case .submitting, .created, .failed:
            true
        }
    }

    var isSubmitting: Bool {
        if case .submitting = self {
            true
        } else {
            false
        }
    }
}
