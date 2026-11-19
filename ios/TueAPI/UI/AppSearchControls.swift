import SwiftUI

struct AppFilterMenuButton<SelectionValue: Hashable, Option: Identifiable>: View {
    let title: String
    let anyLabel: String
    let options: [Option]
    @Binding var selection: SelectionValue?
    let optionLabel: (Option) -> String
    let optionValue: (Option) -> SelectionValue
    var isLoading = false
    var onSelectionChanged: ((SelectionValue?) -> Void)? = nil

    private var selectedLabel: String {
        guard let selection,
              let option = options.first(where: { optionValue($0) == selection }) else {
            return anyLabel
        }
        return optionLabel(option)
    }

    var body: some View {
        Menu {
            Button {
                updateSelection(nil)
            } label: {
                menuRow(anyLabel, isSelected: selection == nil)
            }

            ForEach(options) { option in
                let value = optionValue(option)
                Button {
                    updateSelection(value)
                } label: {
                    menuRow(optionLabel(option), isSelected: selection == value)
                }
            }
        } label: {
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)

                HStack(spacing: 12) {
                    Text(selectedLabel)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.primary)
                        .lineLimit(1)

                    Spacer(minLength: 0)

                    Image(systemName: "chevron.up.chevron.down")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
        .buttonStyle(.plain)
        .disabled(isLoading)
    }

    private func menuRow(_ label: String, isSelected: Bool) -> some View {
        HStack {
            Text(label)
            Spacer()
            if isSelected {
                Image(systemName: "checkmark")
            }
        }
    }

    private func updateSelection(_ newValue: SelectionValue?) {
        selection = newValue
        onSelectionChanged?(newValue)
    }
}

struct AppSearchActionRow: View {
    let searchTitle: String
    let isSearching: Bool
    let isSearchDisabled: Bool
    let isResetDisabled: Bool
    let onSearch: () -> Void
    let onReset: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Button("Reset", action: onReset)
                .buttonStyle(.bordered)
                .disabled(isResetDisabled)

            Spacer()

            Button(action: onSearch) {
                HStack(spacing: 8) {
                    if isSearching {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Image(systemName: "magnifyingglass")
                    }
                    Text(searchTitle)
                }
            }
            .studentProminentButton()
            .disabled(isSearchDisabled)
        }
    }
}
