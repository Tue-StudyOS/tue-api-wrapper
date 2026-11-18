import SwiftUI

struct TodayCancellationsCard: View {
    let events: [LectureEvent]
    let model: AppModel

    var body: some View {
        if !events.isEmpty {
            AppSurfaceCard {
                HStack {
                    Label("Cancelled lectures", systemImage: "calendar.badge.minus")
                        .font(.headline)
                    Spacer()
                    NavigationLink("Schedule") {
                        CalendarScheduleView(model: model)
                    }
                    .font(.subheadline.weight(.semibold))
                }
                ForEach(events.prefix(3)) { event in
                    NavigationLink(value: event) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(event.title).font(.subheadline.weight(.semibold))
                            Text(event.timeRangeText).font(.footnote).foregroundStyle(.secondary)
                            if let reason = event.cancellationReason, !reason.isEmpty {
                                Text(reason).font(.footnote).foregroundStyle(.secondary)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

struct TodayDocumentsLink: View {
    let model: AppModel

    var body: some View {
        NavigationLink {
            StudentDocumentsView(model: model)
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "doc.text")
                VStack(alignment: .leading, spacing: 3) {
                    Text("Documents").font(.headline)
                    Text("Certificates and official reports").font(.subheadline).foregroundStyle(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right").font(.footnote.weight(.semibold))
            }
            .foregroundStyle(.primary)
        }
        .padding(20)
        .background(Color(uiColor: .systemBackground), in: RoundedRectangle(cornerRadius: 18))
    }
}
