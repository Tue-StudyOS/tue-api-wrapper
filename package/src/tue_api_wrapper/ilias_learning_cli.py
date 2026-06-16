from __future__ import annotations

import argparse
import sys

from .config import AlmaError
from .credentials import read_uni_credentials
from .ilias_client import IliasClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Request-based Ovidius readers for forum topics and exercise assignments."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    forum = subparsers.add_parser("forum", help="Print forum topics.")
    forum.add_argument("--target", default="frm/5509946", help="ILIAS forum target or full URL.")
    forum.add_argument("--limit", type=int, default=25, help="Maximum number of topics to print.")

    exercise = subparsers.add_parser("exercise", help="Print exercise assignments.")
    exercise.add_argument("--target", default="exc/5509760", help="ILIAS exercise target or full URL.")
    exercise.add_argument("--limit", type=int, default=25, help="Maximum number of assignments to print.")

    course = subparsers.add_parser("course-assignments", help="Print assignments grouped by exercise in a course.")
    course.add_argument("--target", default="crs/5551408", help="ILIAS course target or full URL.")
    course.add_argument("--limit", type=int, default=25, help="Maximum number of assignments to print.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    username, password = read_uni_credentials()
    if not username or not password:
        parser.error(
            "Set UNI_USERNAME and UNI_PASSWORD in the environment first. "
            "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
        )

    client = IliasClient()
    try:
        client.login(username=username, password=password)
        if args.command == "forum":
            topics = client.fetch_forum_topics(args.target)
            for topic in topics[: args.limit]:
                print(
                    f"- {topic.title} | author={topic.author or '-'} | posts={topic.posts or '-'} | "
                    f"last={topic.last_post or '-'} | visits={topic.visits or '-'} | {topic.url}"
                )
            return 0

        if args.command == "exercise":
            assignments = client.fetch_exercise_assignments(args.target)
            for assignment in assignments[: args.limit]:
                print(
                    f"- {assignment.title} | due={assignment.due_at or assignment.due_hint or '-'} | "
                    f"status={assignment.status or '-'} | type={assignment.submission_type or '-'} | {assignment.url}"
                )
            return 0

        if args.command == "course-assignments":
            page = client.fetch_course_assignments(args.target)
            printed = 0
            print(page.course.title)
            for group in page.exercises:
                print(f"{group.exercise.kind or 'Exercise'}: {group.exercise.label}")
                for assignment in group.assignments:
                    if printed >= args.limit:
                        return 0
                    print(
                        f"- {assignment.title} | due={assignment.due_at or assignment.due_hint or '-'} | "
                        f"status={assignment.status or '-'} | type={assignment.submission_type or '-'} | {assignment.url}"
                    )
                    printed += 1
            if printed == 0:
                print("No exercise assignments were found for this course.")
            return 0
    except AlmaError as exc:
        print(f"ilias error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
