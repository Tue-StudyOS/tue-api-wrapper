import SwiftUI

struct EnrollmentRecordRow: View {
    var record: AlmaEnrollmentRecord

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(record.title)
                        .font(.headline)
                    Text(metadataText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer(minLength: 8)

                if let status = record.status?.trimmedOrNil {
                    Text(status)
                        .font(.caption.weight(.semibold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .foregroundStyle(statusTint)
                        .background(statusTint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8))
                }
            }

            if let schedule = record.scheduleText?.trimmedOrNil {
                Label {
                    Text(schedule)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                        .textSelection(.enabled)
                } icon: {
                    Image(systemName: record.category == "Prüfung" ? "calendar.badge.clock" : "calendar")
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }

    private var metadataText: String {
        [
            record.category?.trimmedOrNil,
            record.eventType?.trimmedOrNil,
            record.number?.trimmedOrNil,
            record.semester?.trimmedOrNil,
            record.attempt?.trimmedOrNil.map { "Attempt \($0)" }
        ]
            .compactMap { $0 }
            .joined(separator: " · ")
            .trimmedOrNil ?? "No structured metadata"
    }

    private var statusTint: Color {
        let value = record.status?.lowercased() ?? ""
        if value.contains("zugelassen") || value.contains("angemeldet") {
            return .green
        }
        if value.contains("storniert") || value.contains("abgemeldet") {
            return .orange
        }
        return .secondary
    }
}
