import AVFoundation
import SwiftUI

struct DeutschlandTicketView: View {
    var model: AppModel

    private let store: DeutschlandTicketStore?
    @State private var ticket: DeutschlandTicket?
    @State private var isScannerPresented = false
    @State private var errorMessage: String?

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
            .padding(.bottom, 124)
        }
        .background(Color(uiColor: .systemGroupedBackground))
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
            KufBarcodeScannerView(
                onScan: saveScan,
                onError: showScannerError,
                preferredMetadataTypes: [.aztec, .pdf417, .qr],
                cameraDeniedMessage: "Camera access is needed to scan your Deutschlandticket barcode."
            )
            .ignoresSafeArea()
        }
        .alert("Deutschlandticket", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "")
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Deutschlandticket")
                .font(.system(.largeTitle, design: .rounded, weight: .bold))
            Text("StudyOS stores and displays this barcode locally on this device. It does not validate official ticket status.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
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
            .buttonStyle(.borderedProminent)
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
            .buttonStyle(.borderedProminent)

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
            LabeledContent("Validation", value: "Not checked by StudyOS")
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
