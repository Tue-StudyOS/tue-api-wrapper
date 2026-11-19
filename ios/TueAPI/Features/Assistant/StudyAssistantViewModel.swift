#if canImport(FoundationModels)
import Foundation
import FoundationModels
import Observation

@available(iOS 26.0, *)
@Observable
@MainActor
final class StudyAssistantViewModel {
    let configuration: StudyAssistantConfiguration

    var draft = ""
    var messages: [StudyAssistantMessage]
    var isSending = false
    var statusMessage: String?

    private let model = SystemLanguageModel.default
    private var session: LanguageModelSession?

    init(configuration: StudyAssistantConfiguration) {
        self.configuration = configuration
        self.messages = [
            StudyAssistantMessage(
                role: .assistant,
                text: "Ask about your grades, current study status, courses, or upcoming talks. The assistant uses Apple’s on-device model with a small set of live university tools."
            )
        ]
    }

    var canSend: Bool {
        !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !isSending
            && model.isAvailable
    }

    var availabilityMessage: String? {
        switch model.availability {
        case .available:
            return nil
        case .unavailable(.deviceNotEligible):
            return "The device is not eligible for Apple Intelligence."
        case .unavailable(.appleIntelligenceNotEnabled):
            return "Apple Intelligence is not enabled on this device."
        case .unavailable(.modelNotReady):
            return "The on-device model is not ready yet."
        case .unavailable(_):
            return "The on-device model is unavailable."
        }
    }

    func prepare() {
        guard case .available = model.availability else { return }
        if session == nil {
            session = makeSession()
            session?.prewarm()
        }
    }

    func resetConversation() {
        session = nil
        statusMessage = nil
        draft = ""
        messages = [
            StudyAssistantMessage(
                role: .assistant,
                text: "Conversation cleared. Ask a fresh question about grades, study status, courses, or talks."
            )
        ]
        prepare()
    }

    func sendCurrentDraft() async {
        let input = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !input.isEmpty else { return }
        draft = ""
        await send(messageText: input)
    }

    func sendSuggestedPrompt(_ prompt: String) async {
        guard !isSending else { return }
        draft = ""
        await send(messageText: prompt)
    }

    private func send(messageText: String) async {
        guard case .available = model.availability else {
            statusMessage = availabilityMessage
            return
        }

        let session = resolvedSession()
        let transcriptStart = session.transcript.endIndex
        let responseID = UUID()

        isSending = true
        statusMessage = "Running the on-device study assistant."
        messages.append(StudyAssistantMessage(role: .user, text: messageText))
        messages.append(StudyAssistantMessage(id: responseID, role: .assistant, text: "", isPending: true))

        do {
            let prompt = """
            Today is \(Self.promptDateFormatter.string(from: Date())).
            User request: \(messageText)
            """
            let stream = session.streamResponse(to: prompt)

            for try await snapshot in stream {
                updateAssistantMessage(id: responseID, text: snapshot.content, isPending: true)
            }

            let newEntries = Array(session.transcript[transcriptStart..<session.transcript.endIndex])
            let toolNames = toolNames(from: newEntries)
            updateAssistantMessage(id: responseID, text: currentAssistantText(id: responseID), toolNames: toolNames, isPending: false)
            statusMessage = toolNames.isEmpty ? nil : "Used \(toolNames.joined(separator: ", "))."
        } catch {
            updateAssistantMessage(
                id: responseID,
                text: "Assistant request failed: \(error.localizedDescription)",
                toolNames: [],
                isPending: false
            )
            statusMessage = error.localizedDescription
        }

        isSending = false
    }

    private func resolvedSession() -> LanguageModelSession {
        if let session {
            return session
        }
        let freshSession = makeSession()
        session = freshSession
        return freshSession
    }

    private func makeSession() -> LanguageModelSession {
        LanguageModelSession(
            model: model,
            tools: makeStudyAssistantTools(configuration: configuration),
            instructions: """
            You are the TUE study assistant inside an iOS app.
            Use tools for live university data instead of guessing.
            Keep answers concise and practical.
            Mention the source system when it matters, such as Alma, ILIAS, Moodle, or the talks calendar.
            Never invent grades, courses, talks, deadlines, or lecture times.
            """
        )
    }

    private func currentAssistantText(id: UUID) -> String {
        messages.first(where: { $0.id == id })?.text ?? ""
    }

    private func updateAssistantMessage(
        id: UUID,
        text: String,
        toolNames: [String]? = nil,
        isPending: Bool
    ) {
        guard let index = messages.firstIndex(where: { $0.id == id }) else {
            return
        }
        messages[index].text = text
        if let toolNames {
            messages[index].toolNames = toolNames
        }
        messages[index].isPending = isPending
    }

    private func toolNames(from entries: [Transcript.Entry]) -> [String] {
        var seen = Set<String>()
        var ordered: [String] = []

        for entry in entries {
            switch entry {
            case .toolCalls(let calls):
                for call in calls where seen.insert(call.toolName).inserted {
                    ordered.append(call.toolName)
                }
            case .toolOutput(let output):
                if seen.insert(output.toolName).inserted {
                    ordered.append(output.toolName)
                }
            default:
                break
            }
        }

        return ordered
    }

    private static let promptDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Europe/Berlin")
        formatter.dateStyle = .full
        formatter.timeStyle = .short
        return formatter
    }()
}
#endif
