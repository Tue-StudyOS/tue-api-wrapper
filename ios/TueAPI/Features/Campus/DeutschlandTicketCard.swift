import SwiftUI

struct DeutschlandTicketCard: View {
    let ticket: DeutschlandTicket

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 5) {
                Text("Deutschlandticket")
                    .font(.caption.weight(.semibold))
                    .textCase(.uppercase)
                    .foregroundStyle(Color.black.opacity(0.64))
                Text("Local ticket barcode")
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
                    .font(.system(.body, design: .monospaced, weight: .semibold))
                    .lineLimit(3)
                    .minimumScaleFactor(0.7)
                    .foregroundStyle(.black)
                    .textSelection(.enabled)
                Text("Saved \(ticket.scannedAt.formatted(date: .abbreviated, time: .shortened))")
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
        if let image = KufBarcodeRenderer.image(
            for: ticket.barcodeValue,
            symbology: ticket.symbology
        ) {
            Image(uiImage: image)
                .interpolation(.none)
                .resizable()
                .scaledToFit()
                .frame(maxWidth: .infinity, minHeight: 160, maxHeight: 260)
                .accessibilityLabel("Deutschlandticket barcode")
        } else {
            ContentUnavailableView(
                "Barcode cannot be rendered",
                systemImage: "exclamationmark.triangle",
                description: Text("The saved scanner format is not renderable with this payload.")
            )
            .foregroundStyle(.black)
            .frame(maxWidth: .infinity, minHeight: 160)
        }
    }
}

#Preview {
    DeutschlandTicketCard(
        ticket: DeutschlandTicket(
            barcodeValue: "STUDYOS-DEUTSCHLANDTICKET-LOCAL-TEST",
            symbology: "org.iso.QRCode",
            displayName: "Sebastian Boehler",
            scannedAt: .now
        )
    )
    .padding()
    .background(Color(uiColor: .systemGroupedBackground))
}
