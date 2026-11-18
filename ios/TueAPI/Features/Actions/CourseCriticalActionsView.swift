import SwiftUI

struct CourseCriticalActionsView: View {
    var model: AppModel
    var course: CourseDetailReference

    @State private var phase: CriticalActionLoadPhase = .idle
    @State private var intent: CriticalActionIntent?
    @State private var actionError: String?
    @State private var reviewedOption: AlmaCourseRegistrationOption?

    var body: some View {
        if course.detailURL != nil {
            Section("Actions") {
                Button {
                    Task { await prepareAlmaRegistration() }
                } label: {
                    if phase == .preparing {
                        ProgressView()
                    } else {
                        Label("Prepare Alma registration", systemImage: "person.badge.plus")
                    }
                }
                .disabled(phase.isBusy || phase == .unknown)
                if phase == .unknown, let url = course.detailURL {
                    Link("Check registration in Alma", destination: url)
                }

                actionStatus
            }
            .sheet(item: $intent) { intent in
                CriticalActionConfirmationSheet(
                    intent: intent,
                    isSubmitting: phase == .submitting,
                    errorMessage: actionError,
                    proceed: {
                        Task { await submit(intent) }
                    },
                    cancel: {
                        self.intent = nil
                        actionError = nil
                        phase = .idle
                    }
                )
            }
        }
    }

    @ViewBuilder
    private var actionStatus: some View {
        switch phase {
        case .failed(let message):
            StatusBanner(title: "Action unavailable", message: message, systemImage: "exclamationmark.triangle")
        case .unknown:
            StatusBanner(
                title: "Registration status unknown",
                message: "Check this course in Alma before sending another request.",
                systemImage: "exclamationmark.circle"
            )
        case .completed(let message):
            StatusBanner(title: "Action submitted", message: message, systemImage: "checkmark.circle")
        default:
            EmptyView()
        }
    }

    private func prepareAlmaRegistration() async {
        actionError = nil
        phase = .preparing

        guard let detailURL = course.detailURL else {
            phase = .failed("This course does not expose an Alma detail URL.")
            return
        }

        do {
            let (client, credentials) = try model.almaAccessContext(for: "prepare Alma registration")
            let support = try await client.inspectCourseRegistration(
                detailURL: detailURL,
                credentials: credentials
            )
            guard support.supported else {
                phase = .failed(support.message ?? "This Alma detail page does not expose registration.")
                return
            }
            let options = try await client.prepareCourseRegistration(
                detailURL: detailURL,
                credentials: credentials
            )
            guard options.options.count == 1 else {
                phase = .failed(
                    "Multiple Alma registration paths are available for this course. Open Alma directly to choose one."
                )
                return
            }

            reviewedOption = options.options[0]
            intent = CriticalActionIntent(
                kind: .almaCourseRegistration,
                portal: "Alma",
                title: course.title,
                actionLabel: "Register for Alma course",
                targetURL: options.detailURL,
                endpoint: "Authenticated Alma form flow",
                method: "On-device",
                sideEffects: [
                    "Submits a course-registration request for your signed-in university account from this device.",
                    "Uses this Alma detail page and the university login saved on this device.",
                    "The shared backend does not handle your Alma session."
                ],
                requiredInputs: registrationInputs(status: support.status, option: options.options[0]),
                confirmButtonTitle: "Proceed with registration"
            )
            phase = .ready
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func submit(_ intent: CriticalActionIntent) async {
        guard let detailURL = course.detailURL else {
            actionError = "This course does not expose an Alma detail URL."
            return
        }
        guard intent.kind == .almaCourseRegistration, let reviewedOption else {
            actionError = "This action intent is incomplete. Prepare it again."
            return
        }

        phase = .submitting
        do {
            let (client, credentials) = try model.almaAccessContext(for: "submit Alma registration")
            let result = try await client.registerForCourse(
                detailURL: detailURL,
                credentials: credentials,
                planelementID: reviewedOption.planelementID
            )
            self.intent = nil
            actionError = nil
            switch result.status {
            case "registered":
                phase = .completed(result.messages.first ?? "Alma reports that you are registered.")
            case "not_registered":
                phase = .failed(result.messages.first ?? "Alma reports that you are not registered.")
            default:
                phase = .unknown
            }
        } catch {
            self.intent = nil
            phase = .unknown
        }
    }

    private func registrationInputs(
        status: String?,
        option: AlmaCourseRegistrationOption
    ) -> [String] {
        var inputs: [String] = ["Registration path: \(option.label)"]
        if let status {
            inputs.insert("Current Alma status: \(status)", at: 0)
        }
        return inputs
    }
}
