import SwiftUI

struct KufTicketCard: View {
    let ticket: KufTicket

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 5) {
                Text("Hochschulsport")
                    .font(.caption.weight(.semibold))
                    .textCase(.uppercase)
                    .foregroundStyle(Color.black.opacity(0.64))
                Text("KuF access")
                    .font(.system(.title, design: .rounded, weight: .bold))
                    .foregroundStyle(.black)
                if let displayName = ticket.displayName, !displayName.isEmpty {
                    Text(displayName)
                        .font(.headline)
                        .foregroundStyle(.blue)
                }
            }

            barcode

            VStack(alignment: .leading, spacing: 4) {
                Text(ticket.formattedCode)
                    .font(.system(.title3, design: .monospaced, weight: .semibold))
                    .foregroundStyle(.black)
                    .textSelection(.enabled)
                Text("Scanned \(ticket.scannedAt.formatted(date: .abbreviated, time: .shortened))")
                    .font(.footnote)
                    .foregroundStyle(Color.black.opacity(0.6))
            }
        }
        .padding(22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .strokeBorder(Color.black.opacity(0.12), lineWidth: 1)
        }
        .shadow(color: .black.opacity(0.08), radius: 20, x: 0, y: 10)
    }

    @ViewBuilder
    private var barcode: some View {
        if let image = KufBarcodeRenderer.image(for: ticket) {
            Image(uiImage: image)
                .interpolation(.none)
                .resizable()
                .scaledToFit()
                .frame(maxWidth: .infinity, minHeight: 92, maxHeight: 128)
                .accessibilityLabel("KuF barcode")
        } else {
            ContentUnavailableView(
                "Barcode cannot be rendered",
                systemImage: "exclamationmark.triangle",
                description: Text("The saved scanner format is not renderable with this payload.")
            )
            .foregroundStyle(.black)
            .frame(maxWidth: .infinity, minHeight: 112)
        }
    }
}

#Preview {
    KufTicketCard(
        ticket: KufTicket(
            barcodeValue: "3600728197043",
            symbology: "org.gs1.EAN-13",
            displayName: "Sebastian Böhler",
            scannedAt: .now
        )
    )
    .padding()
    .background(Color(uiColor: .systemGroupedBackground))
}
