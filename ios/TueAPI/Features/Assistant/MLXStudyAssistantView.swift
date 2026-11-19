import SwiftUI

struct MLXStudyAssistantView: View {
    @State private var viewModel: MLXStudyAssistantViewModel
    @FocusState private var isComposerFocused: Bool

    init(configuration: StudyAssistantConfiguration, fallbackReason: String) {
        _viewModel = State(initialValue: MLXStudyAssistantViewModel(configuration: configuration, fallbackReason: fallbackReason))
    }

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 16) {
                    headerCard

                    if viewModel.messages.count <= 1 {
                        suggestionRow
                    }

                    ForEach(viewModel.messages) { message in
                        StudyAssistantChatBubble(message: message)
                            .id(message.id)
                    }
                }
                .padding(16)
            }
            .background(Color(uiColor: .systemGroupedBackground))
            .safeAreaInset(edge: .bottom) {
                composer
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Clear") {
                        viewModel.resetConversation()
                    }
                    .disabled(viewModel.isSending)
                }
            }
            .onChange(of: viewModel.messages) {
                guard let id = viewModel.messages.last?.id else { return }
                withAnimation(.snappy(duration: 0.24)) {
                    proxy.scrollTo(id, anchor: .bottom)
                }
            }
        }
    }

    private var headerCard: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 8) {
                Text("Local MLX assistant")
                    .font(.system(.title2, design: .rounded, weight: .bold))

                Text(viewModel.fallbackReason)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Text("Model: \(MLXStudyAssistantService.defaultModelID)")
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
            }

            if !viewModel.configuration.hasCredentials {
                AppInlineStatusLine(
                    text: "Connect your university account in Settings to answer questions about grades, tasks, deadlines, or lectures.",
                    systemImage: "lock.slash",
                    tint: .orange
                )
            }

            if let statusMessage = viewModel.statusMessage {
                AppInlineStatusLine(
                    text: statusMessage,
                    tint: .accentColor,
                    isLoading: viewModel.isSending
                )
            }

            if let downloadProgress = viewModel.downloadProgress, downloadProgress.totalUnitCount > 0 {
                ProgressView(value: downloadProgress.fractionCompleted) {
                    Text("Model download")
                }
            }
        }
    }

    private var suggestionRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(Self.suggestedPrompts, id: \.self) { prompt in
                    Button(prompt) {
                        isComposerFocused = false
                        Task {
                            await viewModel.sendSuggestedPrompt(prompt)
                        }
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color(uiColor: .secondarySystemBackground), in: Capsule())
                }
            }
        }
    }

    private var composer: some View {
        VStack(spacing: 0) {
            Divider()

            HStack(alignment: .bottom, spacing: 12) {
                TextField("Ask using local Qwen", text: $viewModel.draft, axis: .vertical)
                    .textInputAutocapitalization(.sentences)
                    .autocorrectionDisabled()
                    .focused($isComposerFocused)
                    .lineLimit(1...5)
                    .submitLabel(.send)
                    .onSubmit {
                        guard viewModel.canSend else { return }
                        isComposerFocused = false
                        Task {
                            await viewModel.sendCurrentDraft()
                        }
                    }

                Button {
                    isComposerFocused = false
                    Task {
                        await viewModel.sendCurrentDraft()
                    }
                } label: {
                    Image(systemName: viewModel.isSending ? "hourglass" : "arrow.up.circle.fill")
                        .font(.system(size: 28))
                }
                .buttonStyle(.plain)
                .disabled(!viewModel.canSend)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(.ultraThinMaterial)
        }
    }

    private static let suggestedPrompts = [
        "What is currently due for me?",
        "Summarize my current grades.",
        "Find machine learning courses.",
        "Any upcoming AI talks?"
    ]
}
