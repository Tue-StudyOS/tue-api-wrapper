from __future__ import annotations

from pathlib import Path
from typing import Any

from .portal_common import serialize
from .study_radar import collect_study_radar
from .study_radar_runtime import make_client, state_path
from .study_radar_state import compare_and_save
from .study_timetable import collect_timetable
from .agent_course_search import search_courses_live
from .ilias_forum_threads import validate_forum_target


def register_study_tools(server: Any, env_file: str | Path | None) -> None:
    def run(operation):
        client, username = make_client(env_file)
        try:
            return operation(client, username)
        finally:
            client.close()

    @server.tool()
    def study_course_search(query: str, term: str | None = None, limit: int = 20, moodle_offset: int = 0) -> dict[str, Any]:
        """Search Alma, ILIAS and the Moodle catalogue independently; results are unmerged candidates."""
        return run(lambda client, _: search_courses_live(client, query, term=term, limit=limit, moodle_offset=moodle_offset))

    @server.tool()
    def study_radar_read(days: int = 30, limit: int = 50, term: str | None = None) -> dict[str, Any]:
        """Read bounded Alma timetable and notices, ILIAS assignments and quizzes, and Moodle deadlines. Check each source status."""
        return run(lambda client, _: collect_study_radar(client, days=days, limit=limit, term=term))

    @server.tool()
    def study_radar_changes(days: int = 30, limit: int = 50, term: str | None = None) -> dict[str, Any]:
        """Compare against and update a private local snapshot. First run establishes a baseline; removals are not inferred."""
        return run(lambda client, username: compare_and_save(
            collect_study_radar(client, days=days, limit=limit, term=term), state_path(username)))

    @server.tool()
    def study_timetable(days: int = 30, limit: int = 50, term: str | None = None) -> dict[str, Any]:
        """Read upcoming Alma timetable occurrences, including coverage and identity warnings."""
        return run(lambda client, _: collect_timetable(client.alma, term=term, days=days, limit=limit))

    @server.tool()
    def study_alma_notices() -> dict[str, Any]:
        """Read Alma portal messages; notices are not necessarily deadlines."""
        return run(lambda client, _: serialize(client.alma.portal_messages()))

    @server.tool()
    def study_ilias_assignment_deadlines(course_limit: int = 20, assignment_limit: int = 50) -> dict[str, Any]:
        """Read bounded ILIAS assignment metadata across directly listed exercises."""
        return run(lambda client, _: {"items": serialize(client.ilias.assignment_deadlines(course_limit=course_limit, assignment_limit=assignment_limit))})

    @server.tool()
    def study_mail_message(uid: str, mailbox: str = "INBOX") -> dict[str, Any]:
        """Read one university mail message by mailbox and UID."""
        return run(lambda client, _: serialize(client.mail.message(uid, mailbox=mailbox)))

    @server.tool()
    def study_moodle_grades() -> dict[str, Any]:
        """Read available Moodle grades and feedback summaries."""
        return run(lambda client, _: serialize(client.moodle.grades()))

    @server.tool()
    def study_alma_exams() -> dict[str, Any]:
        """Read Alma exam overview; course membership is not proof of exam registration."""
        return run(lambda client, _: {"items": serialize(client.alma.exams())})

    @server.tool()
    def study_alma_enrollments() -> dict[str, Any]:
        """Read the Alma course enrollment page for the signed-in student."""
        return run(lambda client, _: serialize(client.alma.enrollments()))

    @server.tool()
    def study_ilias_memberships() -> dict[str, Any]:
        """List the student's ILIAS memberships."""
        return run(lambda client, _: {"items": serialize(client.ilias.memberships())})

    @server.tool()
    def study_ilias_content(target: str) -> dict[str, Any]:
        """Read first-level ILIAS course or folder contents for a target URL or ID."""
        return run(lambda client, _: serialize(client.ilias.content(target)))

    @server.tool()
    def study_ilias_forum(target: str) -> dict[str, Any]:
        """List visible ILIAS forum topics; this does not read individual posts."""
        return run(lambda client, _: {'items': serialize(client.ilias.forum_topics(validate_forum_target(target)))})

    @server.tool()
    def study_ilias_thread(target: str) -> dict[str, Any]:
        """Read an ILIAS discussion by its viewThread URL, without following post action links."""
        return run(lambda client, _: serialize(client.ilias.forum_thread(target)))

    @server.tool()
    def study_moodle_courses(limit: int = 24, offset: int = 0) -> dict[str, Any]:
        """List enrolled Moodle courses with pagination."""
        return run(lambda client, _: serialize(client.moodle.courses(limit=limit, offset=offset)))

    @server.tool()
    def study_moodle_content(course_id: int) -> dict[str, Any]:
        """Read visible course sections, activities and explicitly linked Alma/ILIAS pages; links may be sensitive."""
        return run(lambda client, _: serialize(client.moodle.course_content(course_id)))

    @server.tool()
    def study_moodle_forum(forum_id: int, page: int = 0) -> dict[str, Any]:
        """Read visible Moodle forum discussions and pagination links."""
        return run(lambda client, _: serialize(client.moodle.forum(forum_id, page=page)))

    @server.tool()
    def study_moodle_discussion(discussion_id: int) -> dict[str, Any]:
        """Read visible posts and replies in a Moodle discussion."""
        return run(lambda client, _: serialize(client.moodle.discussion(discussion_id)))

    @server.tool()
    def study_moodle_quiz(quiz_id: int) -> dict[str, Any]:
        """Read a Moodle quiz overview without starting an attempt."""
        return run(lambda client, _: serialize(client.moodle.quiz(quiz_id)))

    @server.tool()
    def study_moodle_quiz_attempt(attempt_id: int, page: int = 0) -> dict[str, Any]:
        """Read visible questions in an existing in-progress Moodle attempt; does not start or answer it."""
        return run(lambda client, _: serialize(client.moodle.quiz_attempt(attempt_id, page=page)))

    @server.tool()
    def study_moodle_assignment(assignment_id: int) -> dict[str, Any]:
        """Read a Moodle assignment's instructions, displayed status and feedback, without changing it."""
        return run(lambda client, _: serialize(client.moodle.assignment(assignment_id)))

    @server.tool()
    def study_moodle_submission_inspect(assignment_id: int) -> dict[str, Any]:
        """Inspect the current submission form and file limits; opening it may create a Moodle draft area."""
        return run(lambda client, _: serialize(client.moodle.inspect_submission(assignment_id)))

    @server.tool()
    def study_moodle_notifications() -> dict[str, Any]:
        """Read Moodle notifications for the signed-in student."""
        return run(lambda client, _: serialize(client.moodle.notifications()))
