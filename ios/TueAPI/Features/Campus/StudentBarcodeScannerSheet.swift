import SwiftUI

struct StudentBarcodeScannerSheet: View {
    let title: String
    let scanner: KufBarcodeScannerView
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            scanner
                .ignoresSafeArea(edges: .bottom)
                .overlay(alignment: .bottom) {
                    Label("Center the barcode in the camera", systemImage: "barcode.viewfinder")
                        .font(.subheadline.weight(.medium))
                        .padding(14)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
                        .padding(.horizontal)
                        .padding(.bottom, 16)
                        .allowsHitTesting(false)
                }
                .navigationTitle(title)
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") { dismiss() }
                    }
                }
        }
    }
}
