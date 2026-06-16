from __future__ import annotations

from fastapi import APIRouter, Query

from .api_errors import translate_alma_error
from .config import AlmaError
from .portal_service import PortalService, serialize

router = APIRouter()
portal_service = PortalService()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


@router.get("/api/ilias/root")
def ilias_root() -> dict[str, object]:
    try:
        return serialize(portal_service._ilias_client().fetch_root_page())
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/memberships")
def ilias_memberships(limit: int = Query(20, ge=1, le=100)) -> list[object]:
    try:
        return serialize(portal_service._ilias_client().fetch_membership_overview()[:limit])
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/tasks")
def ilias_tasks(limit: int = Query(20, ge=1, le=100)) -> list[object]:
    try:
        return serialize(portal_service._ilias_client().fetch_task_overview()[:limit])
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/content")
def ilias_content(target: str) -> dict[str, object]:
    try:
        return serialize(portal_service._ilias_client().fetch_content_page(target))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/forum")
def ilias_forum(target: str) -> list[object]:
    try:
        return serialize(portal_service._ilias_client().fetch_forum_topics(target))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/exercise")
def ilias_exercise(target: str) -> list[object]:
    try:
        return serialize(portal_service._ilias_client().fetch_exercise_assignments(target))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/course-assignments")
def ilias_course_assignments(target: str) -> dict[str, object]:
    try:
        return serialize(portal_service._ilias_client().fetch_course_assignments(target))
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/ilias/assignment-deadlines")
def ilias_assignment_deadlines(
    course_limit: int = Query(20, ge=1, le=100),
    assignment_limit: int = Query(50, ge=1, le=200),
) -> list[object]:
    try:
        return serialize(
            portal_service._ilias_client().fetch_assignment_deadlines(
                course_limit=course_limit,
                assignment_limit=assignment_limit,
            )
        )
    except AlmaError as error:
        raise _translate_error(error) from error
