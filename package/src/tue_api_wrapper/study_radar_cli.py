from __future__ import annotations

import argparse
import json
import sys

from .sdk import TuebingenPublicClient
from .study_data_cli import PRIVATE_RESOURCES, PUBLIC_RESOURCES, read_resource
from .study_radar import collect_study_radar
from .study_radar_runtime import make_client, state_path
from .study_radar_state import compare_and_save
from .raw_course_response import get_raw_course_response
from .alma_course_search_raw import fetch_raw_alma_search
from .moodle_course_search import raw_moodle_course_search
from .ilias_search_raw import fetch_raw_ilias_search
from .raw_interactions import raw_interaction


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read university data and study radar observations as JSON.")
    parser.add_argument("resource", nargs="?", default="radar", choices=sorted({"radar", "raw-course", "raw-interaction", "raw-alma-search", "raw-moodle-search", "raw-ilias-search"} | PRIVATE_RESOURCES | PUBLIC_RESOURCES))
    parser.add_argument("--days", type=int, default=30, help="Moodle and timetable look-ahead in days.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum courses and items per source.")
    parser.add_argument("--env-file", default=".env", help="Local credential file.")
    parser.add_argument("--changes", action="store_true", help="Compare and update the local snapshot.")
    parser.add_argument("--term", help="Exact Alma timetable term label; defaults to the current term.")
    parser.add_argument("--target", help="ILIAS target, Moodle course ID, mail message UID, or advising page URL.")
    parser.add_argument("--mailbox", default="INBOX", help="Mailbox for a mail-message UID.")
    parser.add_argument("--query", default="", help="Search term for the selected resource.")
    parser.add_argument("--degree", action="append", default=[], help="Alma degree filter value; repeat for multiple values.")
    parser.add_argument("--subject", action="append", default=[], help="Alma subject filter value; repeat for multiple values.")
    parser.add_argument("--element-type", action="append", default=[], help="Alma element-type filter value; repeat for multiple values.")
    parser.add_argument("--offset", type=int, default=0, help="Moodle course pagination offset.")
    parser.add_argument("--service", choices=("moodle", "ilias"), help="Service for an explicit raw course read.")
    parser.add_argument("--kind", choices=("forum", "discussion", "quiz", "attempt"), help="Raw interaction page kind.")
    parser.add_argument("--form-only", action="store_true", help="Return the Alma or ILIAS search form without submitting it.")
    parser.add_argument("--page", type=int, default=0, help="Zero-based Moodle search, forum, or quiz attempt page.")
    args = parser.parse_args(argv)
    if args.days < 1 or args.limit < 1 or args.offset < 0:
        parser.error("--days and --limit must be positive and --offset nonnegative")
    if args.resource in {"content", "mail-message", "ilias-forum", "ilias-thread"} and not args.target:
        parser.error(f"{args.resource} requires --target")
    if args.resource in {"moodle-content", "moodle-assignment", "moodle-submission-inspect", "moodle-forum", "moodle-discussion", "moodle-quiz", "moodle-attempt"} and (not args.target or not args.target.isascii() or not args.target.isdigit() or int(args.target) < 1):
        parser.error(f"{args.resource} requires a positive numeric ID as --target")
    if args.resource == "course-search" and not args.query.strip():
        parser.error("course-search requires --query")
    if args.resource == "alma-program-search" and not (args.query.strip() or args.degree or args.subject or args.element_type):
        parser.error("alma-program-search requires --degree, --subject, --element-type, or --query")
    if args.resource == "raw-course" and (not args.service or not args.target):
        parser.error("raw-course requires --service and numeric --target")
    if args.resource == "raw-interaction" and (not args.service or not args.kind or not args.target):
        parser.error("raw-interaction requires --service, --kind, and --target")
    if args.resource == "raw-alma-search" and not args.form_only and not args.query.strip():
        parser.error("raw-alma-search requires --query or --form-only")
    if args.resource == "raw-moodle-search" and not args.query.strip():
        parser.error("raw-moodle-search requires --query")
    if args.resource == "raw-ilias-search" and not args.form_only and not args.query.strip():
        parser.error("raw-ilias-search requires --query or --form-only")
    if args.changes and args.resource != "radar":
        parser.error("--changes is only available for radar")
    try:
        if args.resource in PUBLIC_RESOURCES:
            print(json.dumps(read_resource(TuebingenPublicClient(), args), ensure_ascii=False))
            return 0
        client, username = make_client(args.env_file)
        try:
            if args.resource == "raw-interaction":
                result = raw_interaction(client, args.service, args.kind, args.target, page=args.page)
                print(json.dumps(result, ensure_ascii=False))
                return int(not 200 <= result["status_code"] < 300)
            if args.resource == "raw-ilias-search":
                result = fetch_raw_ilias_search(client.ilias.client, query=args.query, form_only=args.form_only)
                print(json.dumps(result, ensure_ascii=False))
                return int(not 200 <= result["status_code"] < 300)
            if args.resource == "raw-moodle-search":
                result = raw_moodle_course_search(client.moodle.client, args.query, page=args.page, per_page=args.limit)
                print(json.dumps(result, ensure_ascii=False))
                return int(not 200 <= result["status_code"] < 300)
            if args.resource == "raw-alma-search":
                result = fetch_raw_alma_search(client.alma.client, query=args.query, term=args.term, form_only=args.form_only)
                print(json.dumps(result, ensure_ascii=False))
                return int(not 200 <= result["status_code"] < 300)
            if args.resource == "raw-course":
                result = get_raw_course_response(client, args.service, args.target)
                print(json.dumps(result, ensure_ascii=False))
                return int(not 200 <= result["status_code"] < 300)
            if args.resource != "radar":
                result = read_resource(client, args)
                print(json.dumps(result, ensure_ascii=False))
                return int(args.resource == "course-search" and any(source["status"] != "ok" for source in result["sources"].values()))
            observation = collect_study_radar(client, days=args.days, limit=args.limit, term=args.term)
        finally:
            client.close()
        result = compare_and_save(observation, state_path(username)) if args.changes else observation
    except Exception as error:
        print(f"university data error: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return int(any(source["status"] != "ok" for source in result["sources"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
