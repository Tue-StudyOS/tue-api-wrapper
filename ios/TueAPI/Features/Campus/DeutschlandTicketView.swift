import AVFoundation
import SwiftUI

struct DeutschlandTicketView: View {
    var model: AppModel

    private let store: DeutschlandTicketStore?
    @State private var ticket: DeutschlandTicket?
    @State private var isScannerPresented = false
    @State private var errorMessage: String?
    @State private var saveCount = 0

    init(model: AppModel, store: DeutschlandTicketStore? = DeutschlandTicketStore()) {
        self.model = model
        self.store = store
        self._ticket = State(initialValue: store?.loadTicket())
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                header

                if let ticket {
                    ticketSection(ticket)
                } else {
                    emptyTicketState
                }
            }
            .padding(16)
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .sensoryFeedback(.success, trigger: saveCount)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    isScannerPresented = true
                } label: {
                    Label(ticket == nil ? "Scan" : "Replace", systemImage: "barcode.viewfinder")
                }
            }
        }
        .sheet(isPresented: $isScannerPresented) {
            StudentBarcodeScannerSheet(
                title: "Scan Deutschlandticket",
                scanner: KufBarcodeScannerView(
                    onScan: saveScan,
                    onError: showScannerError,
                    preferredMetadataTypes: [.aztec, .pdf417, .qr],
                    cameraDeniedMessage: "Camera access is needed to scan your Deutschlandticket barcode."
                )
            )
        }
        .alert("Deutschlandticket", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "")
        }
    }

    private var header: some View {
        StudentScreenHeading(title: "Deutschlandticket", detail: "Show a saved barcode. Check ticket validity with your transport provider.")
    }

    private var emptyTicketState: some View {
        AppSurfaceCard {
            ContentUnavailableView(
                "No ticket saved",
                systemImage: "barcode.viewfinder",
                description: Text("Scan the QR, Aztec, or PDF417 barcode from your ticket.")
            )
            .frame(maxWidth: .infinity)
            .padding(.vertical, 22)

            Button {
                isScannerPresented = true
            } label: {
                Label("Scan ticket", systemImage: "camera.viewfinder")
                    .frame(maxWidth: .infinity)
            }
            .studentProminentButton()
            .controlSize(.large)
        }
    }

    private func ticketSection(_ ticket: DeutschlandTicket) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            DeutschlandTicketCard(ticket: ticket)
            ticketDetails(ticket)

            Button {
                isScannerPresented = true
            } label: {
                Label("Replace", systemImage: "arrow.triangle.2.circlepath")
                    .frame(maxWidth: .infinity)
            }
            .studentProminentButton()

            Button(role: .destructive) {
                deleteTicket()
            } label: {
                Label("Delete", systemImage: "trash")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
        }
        .controlSize(.large)
    }

    private func ticketDetails(_ ticket: DeutschlandTicket) -> some View {
        AppSurfaceCard {
            LabeledContent("Scanner format", value: ticket.symbology)
            LabeledContent("Saved locally", value: ticket.scannedAt.formatted(date: .abbreviated, time: .shortened))
            LabeledContent("Validation", value: "Check with your provider")
        }
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )
    }

    private func saveScan(_ result: KufBarcodeScanResult) {
        let nextTicket = DeutschlandTicket(
            barcodeValue: result.value,
            symbology: result.symbology,
            displayName: model.profileName,
            scannedAt: .now
        )

        guard let store else {
            showScannerError("Local Deutschlandticket storage is unavailable.")
            return
        }

        do {
            try store.save(nextTicket)
            ticket = store.loadTicket()
            isScannerPresented = false
            saveCount += 1
        } catch {
            showScannerError(error.localizedDescription)
        }
    }

    private func showScannerError(_ message: String) {
        isScannerPresented = false
        errorMessage = message
    }

    private func deleteTicket() {
        store?.deleteTicket()
        ticket = nil
    }
}

#Preview {
    NavigationStack {
        DeutschlandTicketView(model: AppModel(), store: nil)
    }
}
