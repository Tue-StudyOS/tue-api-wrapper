import SwiftUI

struct KufTicketView: View {
    var model: AppModel

    private let onClose: (() -> Void)?
    private let store: KufTicketStore?
    @State private var tickets: [KufTicket]
    @State private var isScannerPresented = false
    @State private var errorMessage: String?

    init(model: AppModel, store: KufTicketStore? = KufTicketStore(), onClose: (() -> Void)? = nil) {
        self.model = model
        self.store = store
        self.onClose = onClose
        self._tickets = State(initialValue: store?.loadTickets() ?? [])
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                if tickets.isEmpty {
                    emptyTicketState
                } else {
                    ForEach(tickets) { ticket in
                        ticketSection(ticket)
                    }
                }
            }
            .padding(16)
            .padding(.bottom, 124)
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("KuF pass")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if let onClose {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done", action: onClose)
                }
            }
            if !tickets.isEmpty {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        isScannerPresented = true
                    } label: {
                        Label("Add barcode", systemImage: "barcode.viewfinder")
                    }
                }
            }
        }
        .sheet(isPresented: $isScannerPresented) {
            KufBarcodeScannerView(
                onScan: saveScan,
                onError: showScannerError
            )
            .ignoresSafeArea()
        }
        .privacySensitive()
        .alert("KuF pass", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "")
        }
    }

    private var emptyTicketState: some View {
        AppSurfaceCard {
            ContentUnavailableView(
                "No card saved",
                systemImage: "barcode.viewfinder",
                description: Text("Scan the barcode from your Hochschulsport confirmation.")
            )
            .frame(maxWidth: .infinity)
            .padding(.vertical, 22)

            Button {
                isScannerPresented = true
            } label: {
                Label("Scan barcode", systemImage: "camera.viewfinder")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
    }

    private func ticketSection(_ ticket: KufTicket) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            KufTicketCard(ticket: ticket)
            ticketDetails(ticket)

            Button(role: .destructive) {
                deleteTicket(ticket)
            } label: {
                Label("Delete", systemImage: "trash")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
        }
        .controlSize(.large)
    }

    private func ticketDetails(_ ticket: KufTicket) -> some View {
        AppSurfaceCard {
            LabeledContent("Scanner format", value: ticket.symbology)
            LabeledContent("Saved locally", value: ticket.scannedAt.formatted(date: .abbreviated, time: .shortened))
        }
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )
    }

    private func saveScan(_ result: KufBarcodeScanResult) {
        let existingTicket = tickets.first {
            $0.matches(barcodeValue: result.value, symbology: result.symbology)
        }
        let nextTicket = KufTicket(
            barcodeValue: result.value,
            symbology: result.symbology,
            displayName: existingTicket?.displayName ?? model.profileName,
            scannedAt: .now
        )

        guard let store else {
            showScannerError("Local KuF card storage is unavailable.")
            return
        }

        do {
            try store.save(nextTicket)
            tickets = store.loadTickets()
            isScannerPresented = false
        } catch {
            showScannerError(error.localizedDescription)
        }
    }

    private func showScannerError(_ message: String) {
        isScannerPresented = false
        errorMessage = message
    }

    private func deleteTicket(_ ticket: KufTicket) {
        do {
            try store?.deleteTicket(ticket)
            tickets = store?.loadTickets() ?? []
        } catch {
            showScannerError(error.localizedDescription)
        }
    }
}

#Preview {
    NavigationStack {
        KufTicketView(model: AppModel(), store: nil)
    }
}
