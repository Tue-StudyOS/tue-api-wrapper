import SwiftUI

struct CampusFoodHeader: View {
    let subtitle: String

    var body: some View {
        StudentScreenHeading(title: "Campus food", detail: subtitle)
    }
}

struct CampusFoodControlsCard: View {
    @Binding var selectedDate: Date
    let isLoading: Bool

    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 12) {
                Text("Meal plan date")
                    .font(.headline)

                DatePicker(
                    "Meal plan date",
                    selection: $selectedDate,
                    displayedComponents: .date
                )
                .datePickerStyle(.compact)
                .labelsHidden()

                Text("The feed is filtered on the backend to the selected Tübingen canteen date.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                if isLoading {
                    AppInlineStatusLine(
                        text: "Refreshing live my-stuwe menus.",
                        tint: .accentColor,
                        isLoading: true
                    )
                }
            }
        }
    }
}

struct CampusFoodCanteenCard: View {
    let canteen: CampusFoodPlanCanteen

    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(canteen.canteen)
                            .font(.headline)

                        if let address = canteen.address, !address.isEmpty {
                            Label(address, systemImage: "mappin.and.ellipse")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }

                    Spacer(minLength: 0)

                    CampusFoodSourceLinks(
                        pageURL: validURL(canteen.pageURL),
                        mapURL: validURL(canteen.mapURL)
                    )
                }

                VStack(spacing: 14) {
                    ForEach(Array(canteen.menus.enumerated()), id: \.element.id) { index, menu in
                        if index > 0 {
                            Divider()
                        }
                        CampusFoodMenuCard(menu: menu)
                    }
                }
            }
        }
    }
}

struct CampusFoodSkeletonCard: View {
    var body: some View {
        AppSurfaceCard {
            VStack(alignment: .leading, spacing: 12) {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Color.secondary.opacity(0.14))
                    .frame(width: 180, height: 18)

                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Color.secondary.opacity(0.1))
                    .frame(height: 14)

                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Color.secondary.opacity(0.1))
                    .frame(height: 14)

                HStack(spacing: 8) {
                    ForEach(0..<3, id: \.self) { _ in
                        Capsule()
                            .fill(Color.secondary.opacity(0.12))
                            .frame(width: 72, height: 28)
                    }
                }
            }
        }
        .redacted(reason: .placeholder)
    }
}

private struct CampusFoodMenuCard: View {
    let menu: CampusFoodMenu

    private var tags: [String] {
        Array(Set((menu.icons + menu.filtersInclude).map { $0.uppercased() })).sorted()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let menuLine = menu.menuLine, !menuLine.isEmpty {
                Text(menuLine)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.secondary)
            }

            VStack(alignment: .leading, spacing: 6) {
                ForEach(menu.items, id: \.self) { item in
                    Text("• \(item)")
                        .font(.body)
                }
            }

            CampusFoodPriceRow(menu: menu)

            if !tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(tags, id: \.self) { tag in
                            CampusFoodPill(text: tag, tint: .green.opacity(0.18))
                        }
                    }
                }
            }

            if !menu.allergens.isEmpty {
                CampusFoodMetadataLine(label: "Allergens", values: menu.allergens)
            }

            if !menu.additives.isEmpty {
                CampusFoodMetadataLine(label: "Additives", values: menu.additives)
            }

            if !menu.meats.isEmpty {
                CampusFoodMetadataLine(label: "Meat markers", values: menu.meats)
            }
        }
    }
}

private struct CampusFoodPriceRow: View {
    let menu: CampusFoodMenu

    var body: some View {
        HStack(spacing: 8) {
            if let studentPrice = menu.studentPrice, !studentPrice.isEmpty {
                CampusFoodPill(text: "Student \(studentPrice) €", tint: .accentColor.opacity(0.16))
            }
            if let guestPrice = menu.guestPrice, !guestPrice.isEmpty {
                CampusFoodPill(text: "Guest \(guestPrice) €", tint: .secondary.opacity(0.14))
            }
            if let pupilPrice = menu.pupilPrice, !pupilPrice.isEmpty {
                CampusFoodPill(text: "Pupil \(pupilPrice) €", tint: .orange.opacity(0.16))
            }
        }
        .font(.footnote.weight(.semibold))
    }
}

private struct CampusFoodMetadataLine: View {
    let label: String
    let values: [String]

    var body: some View {
        Text("\(label): \(values.joined(separator: ", "))")
            .font(.footnote)
            .foregroundStyle(.secondary)
    }
}

private struct CampusFoodSourceLinks: View {
    let pageURL: URL?
    let mapURL: URL?

    var body: some View {
        VStack(alignment: .trailing, spacing: 8) {
            if let pageURL {
                Link(destination: pageURL) {
                    Label("my-stuwe", systemImage: "arrow.up.forward.square")
                }
                .font(.footnote.weight(.semibold))
            }

            if let mapURL {
                Link(destination: mapURL) {
                    Label("Map", systemImage: "map")
                }
                .font(.footnote.weight(.semibold))
            }
        }
    }
}

private struct CampusFoodPill: View {
    let text: String
    let tint: Color

    var body: some View {
        Text(text)
            .font(.footnote.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(tint, in: Capsule())
    }
}

private func validURL(_ value: String?) -> URL? {
    guard let value, !value.isEmpty else {
        return nil
    }
    return URL(string: value)
}
