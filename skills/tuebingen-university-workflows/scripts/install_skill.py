#!/usr/bin/env python3
"""Install the bundled skill into an agent provider's skill directory."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


SKILL_NAME = "tuebingen-university-workflows"


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    source = Path(__file__).resolve().parent.parent
    destination = Path(args.destination).expanduser()
    validate_source(source)

    target = destination / SKILL_NAME
    if target.exists() and not args.force:
        print(f"Skill already exists: {target}", file=sys.stderr)
        print("Re-run with --force to replace only this skill.", file=sys.stderr)
        return 2

    destination.mkdir(parents=True, exist_ok=True)
    staging = destination / f".{SKILL_NAME}.installing"
    remove_if_exists(staging)
    shutil.copytree(source, staging, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    backup = destination / f".{SKILL_NAME}.previous"
    remove_if_exists(backup)
    try:
        if target.exists():
            target.replace(backup)
        staging.replace(target)
    except Exception:
        if backup.exists() and not target.exists():
            backup.replace(target)
        raise
    finally:
        remove_if_exists(staging)

    remove_if_exists(backup)
    print(f"Installed {SKILL_NAME} at {target}")
    print_welcome()
    return 0


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "--destination",
        required=True,
        help="Target directory for this agent provider's skills.",
    )
    argument_parser.add_argument("--force", action="store_true", help="Replace an existing copy of this skill.")
    return argument_parser


def validate_source(source: Path) -> None:
    if source.name != SKILL_NAME or not (source / "SKILL.md").is_file():
        raise RuntimeError(f"Expected a {SKILL_NAME} skill directory, got {source}")


def remove_if_exists(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def print_welcome() -> None:
    print("\nWelcome — what would you like to do at the University of Tuebingen?")
    print("1. Plan a semester or course, compare options, or coordinate teaching")
    print("2. Find a course, module, academic contact, recording, or material")
    print("3. Retrieve a timetable, deadlines, tasks, notices, or university mail")
    print("4. Download a transcript, certificate, grade overview, or other Alma document")
    print("5. Inspect or submit a registration, enrolment, waitlist, or booking action")
    print("6. Build a realistic teaching or study-week plan and reduce overload")
    print("7. Something else — describe the outcome you need")
    print("Public searches need no login. For private data, configure credentials locally; do not paste passwords into chat.")


if __name__ == "__main__":
    raise SystemExit(main())
