"""Read selected existing SDK operations for the JSON CLI."""
from __future__ import annotations

from typing import Any

from .portal_common import serialize
from .study_timetable import collect_timetable
from .agent_course_search import search_courses_live
from .connectivity import check_connectivity
from .ilias_forum_threads import validate_forum_target

PUBLIC_RESOURCES = {"buildings", "canteens", "seats", "people", "advising", "advising-discover", "advising-refresh", "advising-search", "rooms", "connectivity", "alma-program-filters", "alma-program-search"}
PRIVATE_RESOURCES = {"timetable", "exams", "enrollments", "notices", "memberships", "content",
                     "assignments", "moodle-courses", "moodle-content", "moodle-assignment", "moodle-submission-inspect", "moodle-forum", "moodle-discussion", "moodle-quiz", "moodle-attempt", "ilias-forum", "ilias-thread", "moodle-notifications", "mail-inbox", "mail-message", "course-search"}


def read_resource(client: Any, args: Any) -> Any:
    operations = {
        "connectivity": check_connectivity,
        "alma-program-filters": lambda: client.alma.module_search_filters(),
        "alma-program-search": lambda: client.alma.search_modules(query=args.query, degrees=tuple(args.degree),
            subjects=tuple(args.subject), element_types=tuple(args.element_type), max_results=args.limit),
        "buildings": lambda: client.campus.buildings(),
        "canteens": lambda: client.campus.canteens(),
        "seats": lambda: client.campus.seat_availability(),
        "people": lambda: client.directory.search(args.query),
        "advising-refresh": lambda: client.directory.refresh_advising(),
        "advising-discover": lambda: client.directory.discover_advising(),
        "advising-search": lambda: client.directory.search_advising(args.query, limit=args.limit),
        "advising": lambda: client.directory.advising_page(args.target) if args.target else client.directory.advising_page(),
        "rooms": lambda: client.anny.resources(query=args.query),
        "timetable": lambda: collect_timetable(client.alma, term=args.term, days=args.days, limit=args.limit),
        "exams": lambda: {"items": client.alma.exams()},
        "enrollments": lambda: client.alma.enrollments(),
        "notices": lambda: client.alma.portal_messages(),
        "memberships": lambda: {"items": client.ilias.memberships()},
        "content": lambda: client.ilias.content(args.target),
        "ilias-forum": lambda: {"items": client.ilias.forum_topics(validate_forum_target(args.target))},
        "ilias-thread": lambda: client.ilias.forum_thread(args.target),
        "assignments": lambda: {"items": client.ilias.assignment_deadlines(course_limit=args.limit, assignment_limit=args.limit)},
        "moodle-courses": lambda: client.moodle.courses(limit=args.limit, offset=args.offset),
        "moodle-content": lambda: client.moodle.course_content(int(args.target)),
        "moodle-assignment": lambda: client.moodle.assignment(int(args.target)),
        "moodle-submission-inspect": lambda: client.moodle.inspect_submission(int(args.target)),
        "moodle-forum": lambda: client.moodle.forum(int(args.target), page=args.page),
        "moodle-discussion": lambda: client.moodle.discussion(int(args.target)),
        "moodle-quiz": lambda: client.moodle.quiz(int(args.target)),
        "moodle-attempt": lambda: client.moodle.quiz_attempt(int(args.target), page=args.page),
        "moodle-notifications": lambda: client.moodle.notifications(),
        "mail-inbox": lambda: client.mail.inbox(limit=args.limit),
        "mail-message": lambda: client.mail.message(args.target, mailbox=args.mailbox),
        "course-search": lambda: search_courses_live(client, args.query, term=args.term, limit=args.limit, moodle_offset=args.offset),
    }
    result = serialize(operations[args.resource]())
    return result if isinstance(result, dict) else {"items": result}
