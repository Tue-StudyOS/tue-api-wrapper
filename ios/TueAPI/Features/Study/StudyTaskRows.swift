import SwiftUI

struct StudyDeadlineRow: View {
    var deadline: MoodleDeadline

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(deadline.title)
                .font(.subheadline.weight(.medium))
                .lineLimit(2)

            HStack(spacing: 8) {
                if let courseName = deadline.courseName {
                    Label(courseName, systemImage: "book.closed")
                }
                if let due = deadline.formattedTime ?? deadline.dueAt {
                    Label(due, systemImage: "clock")
                        .foregroundStyle(.orange)
                }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 2)
    }
}

struct StudyIliasTaskRow: View {
    var task: IliasTask

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Image(systemName: "checklist")
                    .foregroundStyle(Color.accentColor)
                    .font(.caption)
                Text(task.title)
                    .font(.subheadline.weight(.medium))
                    .lineLimit(2)
            }

            if let end = task.end {
                Label(end, systemImage: "clock")
                    .font(.caption)
                    .foregroundStyle(.orange)
            } else if let type = task.itemType {
                Text(type)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 2)
    }
}

struct StudyIliasAssignmentRow: View {
    var deadline: IliasAssignmentDeadline

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            VStack(alignment: .leading, spacing: 7) {
                Text(deadline.assignment.title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.primary)
                    .lineLimit(3)
                    .fixedSize(horizontal: false, vertical: true)

                Text(deadline.courseTitle)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            HStack(alignment: .center, spacing: 8) {
                if let due = deadline.assignment.dueAt ?? deadline.assignment.dueHint {
                    Text(due)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.orange)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(.orange.opacity(0.12), in: Capsule())
                }

                if let status = deadline.assignment.status {
                    Text(status)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(uiColor: .tertiarySystemBackground), in: Capsule())
                }
            }

            if let url = URL(string: deadline.assignment.url) {
                Link(destination: url) {
                    Label("Open submission", systemImage: "arrow.up.forward")
                        .font(.subheadline.weight(.semibold))
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.regular)
            }
        }
        .padding(.vertical, 4)
    }
}

struct StudyDeadlineSkeletonRow: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            SkeletonLine(width: 180, height: 14)
            HStack(spacing: 8) {
                SkeletonLine(width: 96, height: 10)
                SkeletonLine(width: 72, height: 10)
            }
        }
        .padding(.vertical, 4)
    }
}

struct StudyIliasTaskSkeletonRow: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            SkeletonLine(width: 200, height: 14)
            SkeletonLine(width: 82, height: 10)
        }
        .padding(.vertical, 4)
    }
}

struct StudyIliasAssignmentSkeletonRow: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            SkeletonLine(width: 190, height: 14)
            HStack(spacing: 8) {
                SkeletonLine(width: 120, height: 10)
                SkeletonLine(width: 94, height: 10)
            }
        }
        .padding(.vertical, 4)
    }
}

private struct SkeletonLine: View {
    var width: CGFloat
    var height: CGFloat

    var body: some View {
        RoundedRectangle(cornerRadius: 4)
            .fill(Color.secondary.opacity(0.18))
            .frame(width: width, height: height)
    }
}
