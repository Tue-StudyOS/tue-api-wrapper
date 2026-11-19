import SwiftUI

#if canImport(FoundationModels)
import FoundationModels
#endif

struct StudyAssistantEntryView: View {
    var model: AppModel

    var body: some View {
        Group {
#if targetEnvironment(simulator)
            MLXStudyAssistantView(
                configuration: assistantConfiguration,
                fallbackReason: "The iOS Simulator does not provide Apple Intelligence model assets, so this screen is using local MLX instead."
            )
#else
#if canImport(FoundationModels)
            if #available(iOS 26.0, *), SystemLanguageModel.default.isAvailable {
                StudyAssistantView(
                    configuration: assistantConfiguration
                )
            } else {
                MLXStudyAssistantView(
                    configuration: assistantConfiguration,
                    fallbackReason: appleFallbackReason
                )
            }
#else
            MLXStudyAssistantView(
                configuration: assistantConfiguration,
                fallbackReason: "Apple Foundation Models is not available in this build."
            )
#endif
#endif
        }
        .navigationTitle("Assistant")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var assistantConfiguration: StudyAssistantConfiguration {
        StudyAssistantConfiguration(
            portalAPIBaseURLString: model.portalAPIBaseURLString,
            hasCredentials: model.hasCredentials
        )
    }

#if canImport(FoundationModels)
    private var appleFallbackReason: String {
        if #available(iOS 26.0, *) {
            switch SystemLanguageModel.default.availability {
            case .available:
                return "Apple Foundation Models is available."
            case .unavailable(.appleIntelligenceNotEnabled):
                return "Apple Intelligence is not enabled, so this screen is using local MLX instead."
            case .unavailable(.deviceNotEligible):
                return "This device is not eligible for Apple Intelligence, so this screen is using local MLX instead."
            case .unavailable(.modelNotReady):
                return "Apple's on-device model is not ready yet, so this screen is using local MLX instead."
            case .unavailable(_):
                return "Apple Foundation Models is unavailable, so this screen is using local MLX instead."
            }
        }
        return "Apple Foundation Models requires iOS 26, so this screen is using local MLX instead."
    }
#endif
}
