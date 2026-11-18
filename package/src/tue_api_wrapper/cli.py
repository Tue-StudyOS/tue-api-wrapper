from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from .client import AlmaClient
from .config import AlmaError
from .credentials import read_uni_credentials


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Request-based Alma client that prints the timetable for a term."
    )
    parser.add_argument("--term", default="Sommer 2026", help="Exact Alma term label to export.")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of timetable occurrences to print.",
    )
    parser.add_argument(
        "--save-ics",
        type=Path,
        help="Optional path to store the raw iCalendar export.",
    )
    return parser


def _format_occurrence_line(index: int, occurrence) -> str:
    start = occurrence.start.strftime("%Y-%m-%d %H:%M")
    end = occurrence.end.strftime("%Y-%m-%d %H:%M") if occurrence.end else "?"
    location = occurrence.location or "-"
    if occurrence.status == "cancelled":
        reason = f" | {occurrence.cancellation_reason}" if occurrence.cancellation_reason else ""
        return f"{index:02d}. {start} - {end} | {occurrence.summary} | Canceled{reason}"
    return f"{index:02d}. {start} - {end} | {occurrence.summary} | {location}"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    username, password = read_uni_credentials()
    if not username or not password:
        parser.error(
            "Set UNI_USERNAME and UNI_PASSWORD in the environment first. "
            "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
        )

    client = AlmaClient()
    try:
        client.login(username=username, password=password)
        result = client.fetch_timetable_for_term(args.term)
    except AlmaError as exc:
        print(f"alma error: {exc}", file=sys.stderr)
        return 1

    if args.save_ics:
        args.save_ics.parent.mkdir(parents=True, exist_ok=True)
        args.save_ics.write_text(result.raw_ics, encoding="utf-8")

    print(f"Term: {result.term_label} ({result.term_id})")
    print(f"Series: {len(result.events)}")
    print(f"Occurrences: {len(result.occurrences)}")

    if not result.occurrences:
        print("No timetable occurrences were returned for this term.")
        return 0

    for index, occurrence in enumerate(result.occurrences[: args.limit], start=1):
        print(_format_occurrence_line(index, occurrence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
