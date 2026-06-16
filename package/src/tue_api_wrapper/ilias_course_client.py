from __future__ import annotations

from typing import Protocol
from urllib.parse import parse_qs, urlparse

from .ilias_course_models import IliasCourseAssignmentsPage, IliasCourseExerciseAssignments
from .models import IliasContentItem, IliasContentPage, IliasExerciseAssignment

EXERCISE_KINDS = {"übung", "exercise", "exercises"}


class IliasCourseAssignmentClient(Protocol):
    def fetch_content_page(self, target: str) -> IliasContentPage: ...

    def fetch_exercise_assignments(self, target: str) -> tuple[IliasExerciseAssignment, ...]: ...


def fetch_course_assignments(
    client: IliasCourseAssignmentClient,
    target: str,
) -> IliasCourseAssignmentsPage:
    course = client.fetch_content_page(target)
    groups = tuple(
        IliasCourseExerciseAssignments(
            exercise=item,
            assignments=client.fetch_exercise_assignments(item.url),
        )
        for item in _exercise_items(course)
    )
    return IliasCourseAssignmentsPage(course=course, exercises=groups)


def _exercise_items(course: IliasContentPage) -> tuple[IliasContentItem, ...]:
    return tuple(
        item
        for section in course.sections
        for item in section.items
        if _is_exercise_item(item)
    )


def _is_exercise_item(item: IliasContentItem) -> bool:
    kind = (item.kind or "").strip().casefold()
    if kind in EXERCISE_KINDS:
        return True

    parsed = urlparse(item.url)
    path = parsed.path.casefold()
    if "/goto.php/exc/" in path or path.endswith("/goto.php/exc"):
        return True

    query = parse_qs(parsed.query)
    base_class = (query.get("baseClass") or query.get("baseclass") or [""])[0].casefold()
    cmd_class = (query.get("cmdClass") or query.get("cmdclass") or [""])[0].casefold()
    return base_class == "ilexercisehandlergui" or cmd_class == "ilobjexercisegui"
