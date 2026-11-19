import SwiftUI

extension Color {
    static let studentActionFill = Color(red: 0.647, green: 0.118, blue: 0.216)
}

extension View {
    func studentProminentButton() -> some View {
        buttonStyle(.borderedProminent).tint(.studentActionFill)
    }
}
