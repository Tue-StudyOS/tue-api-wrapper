"""Collect bounded, read-only observations from university systems."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import parse_qs, urlparse

from .study_timetable import collect_timetable


def _key(*parts: object) -> str:
    return sha256("\0".join(str(part or "") for part in parts).encode()).hexdigest()


def _assignments(client: Any, limit: int) -> list[dict[str, Any]]:
    return [
        {"id": _assignment_key(row),
         "title": row.assignment.title, "url": row.assignment.url, "course": row.course_title,
         "due": row.assignment.due_at or row.assignment.due_hint, "status": row.assignment.status}
        for row in client.ilias.assignment_deadlines(course_limit=limit, assignment_limit=limit)
    ]


def _assignment_key(row: Any) -> str:
    parsed = urlparse(row.assignment.url)
    assignment_id = parse_qs(parsed.query).get("ass_id", [None])[0]
    return _key("assignment", assignment_id) if assignment_id else _key(row.exercise_url, row.assignment.url)


def _quizzes(client: Any, limit: int) -> list[dict[str, Any]]:
    return [
        {"id": _key(row.course_url, row.quiz.page_url), "title": row.quiz.title,
         "url": row.quiz.page_url, "course": row.course_title, "due": row.quiz.closes_at,
         "opens": row.quiz.opens_at, "completed_attempts": row.quiz.completed_attempts}
        for row in client.ilias.quiz_deadlines(course_limit=limit, quiz_limit=limit)
    ]


def _moodle(client: Any, days: int, limit: int) -> list[dict[str, Any]]:
    page = client.moodle.deadlines(days=days, limit=limit)
    return [
        {"id": _key(event.id if event.id is not None else event.action_url, event.course_id, event.title if event.id is None else ""),
         "title": event.title, "url": event.action_url or page.source_url, "course": event.course_name,
         "due": event.due_at or event.formatted_time, "description": event.description}
        for event in page.items
    ]


def _notices(client: Any) -> list[dict[str, Any]]:
    return [
        {"id": _key(item.id), "title": item.title, "url": item.url,
         "created_at": item.created_at.isoformat() if item.created_at else item.created_at_label}
        for item in client.alma.portal_messages().items
    ]


def collect_study_radar(client: Any, *, days: int = 30, limit: int = 50, term: str | None = None) -> dict[str, Any]:
    if days < 1 or limit < 1:
        raise ValueError("days and limit must be positive")
    operations = {
        "ilias_assignments": lambda: _assignments(client, limit),
        "ilias_quizzes": lambda: _quizzes(client, limit),
        "moodle_deadlines": lambda: _moodle(client, days, limit),
        "alma_notices": lambda: _notices(client),
    }
    sources: dict[str, Any] = {}
    for name, operation in operations.items():
        try:
            items = operation()
            if len({item["id"] for item in items}) != len(items):
                raise ValueError("Source returned duplicate item identities")
            sources[name] = {"status": "ok", "items": items, "coverage": "bounded"}
        except Exception as error:
            sources[name] = {"status": "error", "error": type(error).__name__, "items": []}
    try:
        sources["alma_timetable"] = collect_timetable(client.alma, term=term, days=days, limit=limit)
    except Exception as error:
        sources["alma_timetable"] = {"status": "error", "error": type(error).__name__, "items": []}
    return {"observed_at": datetime.now(timezone.utc).isoformat(),
            "scope": {"lookahead_days": days, "item_and_course_limit": limit, "timetable_term": term}, "sources": sources}
