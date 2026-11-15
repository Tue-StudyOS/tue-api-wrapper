from __future__ import annotations

import argparse
import json
import sys

from .registration_workflows import execute_registration, inspect_registration, prepare_selected, registration_options
from .study_radar_runtime import make_client


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and review Alma registrations.")
    parser.add_argument("operation", choices=("inspect", "options", "prepare", "execute"))
    parser.add_argument("kind", choices=("course", "exam"))
    parser.add_argument("--url", required=True, help="Alma course or exam detail URL")
    parser.add_argument("--exam-id", help="Alma exam unit identifier")
    parser.add_argument("--option", help="Registration path identifier from Alma")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args(argv)
    if args.operation in {"prepare", "execute"} and not args.option:
        parser.error("prepare and execute require --option")
    try:
        client, username = make_client(args.env_file)
        try:
            if args.operation == "inspect":
                print(json.dumps(inspect_registration(client.alma.client, args.kind, args.url, args.exam_id), ensure_ascii=False))
                return 0
            if args.operation == "options":
                print(json.dumps(registration_options(client.alma.client, args.kind, args.url, args.exam_id), ensure_ascii=False))
                return 0
            reviewed = prepare_selected(client.alma.client, username, args.kind, args.url, args.exam_id, args.option)
            print(json.dumps(reviewed, ensure_ascii=False, indent=2), flush=True)
            if args.operation == "prepare":
                return 0
            if not sys.stdin.isatty():
                print("Execution requires an interactive terminal for confirmation.", file=sys.stderr)
                return 1
            if input("Type REGISTER to submit exactly this action: ") != "REGISTER":
                print("Cancelled; nothing submitted.", file=sys.stderr)
                return 1
            result = execute_registration(client.alma.client, reviewed)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result["outcome"] == "confirmed" else 1
        finally:
            client.close()
    except Exception as error:
        print(f"registration error: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
