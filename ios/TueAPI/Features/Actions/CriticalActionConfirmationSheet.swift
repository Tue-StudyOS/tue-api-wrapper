import SwiftUI

struct CriticalActionConfirmationSheet: View {
    var intent: CriticalActionIntent
    var isSubmitting: Bool
    var errorMessage: String?
    var proceed: () -> Void
    var cancel: () -> Void

    var body: some View {
        NavigationStack {
            List {
                StudentListHeading(title: intent.actionLabel, detail: "Review the target and what will change.")
                Section("Destination") {
                    LabeledContent("Portal", value: intent.portal)
                    LabeledContent(
                        "Submission",
                        value: [intent.method, intent.endpoint]
                            .filter { !$0.isEmpty }
                            .joined(separator: " · ")
                    )
                    if let targetURL = intent.targetURL {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Target")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(targetURL.absoluteString)
                                .font(.footnote)
                                .textSelection(.enabled)
                        }
                    }
                }

                Section("What will change") {
                    ForEach(intent.sideEffects, id: \.self) { effect in
                        Label(effect, systemImage: "arrow.right.circle")
                    }
                }

                if !intent.requiredInputs.isEmpty {
                    Section("Required Inputs") {
                        ForEach(intent.requiredInputs, id: \.self) { input in
                            Label(input, systemImage: "checkmark.seal")
                        }
                    }
                }

                if let errorMessage {
                    Section {
                        StatusBanner(
                            title: "Action failed",
                            message: errorMessage,
                            systemImage: "exclamationmark.triangle"
                        )
                    }
                }

                Section {
                    Button {
                        proceed()
                    } label: {
                        if isSubmitting {
                            ProgressView()
                        } else {
                            Text(intent.confirmButtonTitle)
                        }
                    }
                    .disabled(isSubmitting)

                    Button("Cancel", role: .cancel) {
                        cancel()
                    }
                    .disabled(isSubmitting)
                } footer: {
                    Text("Cancel leaves Alma unchanged. Proceed submits the Alma registration request from this device using your saved university session.")
                }
            }
            .navigationTitle("Confirm Action")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
