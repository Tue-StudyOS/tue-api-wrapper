from __future__ import annotations

from typing import Protocol
from urllib.parse import parse_qs, urlparse

from .ilias_course_models import IliasAssignmentDeadline, IliasCourseAssignmentsPage, IliasCourseExerciseAssignments
from .models import IliasContentItem, IliasContentPage, IliasExerciseAssignment, IliasMembershipItem

EXERCISE_KINDS = {"übung", "exercise", "exercises"}
COURSE_KINDS = {"kurs", "course"}


class IliasCourseAssignmentClient(Protocol):
    def fetch_membership_overview(self) -> tuple[IliasMembershipItem, ...]: ...

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


def fetch_assignment_deadlines(
    client: IliasCourseAssignmentClient,
    *,
    course_limit: int = 20,
    assignment_limit: int = 50,
) -> tuple[IliasAssignmentDeadline, ...]:
    deadlines: list[IliasAssignmentDeadline] = []
    courses = _course_memberships(client.fetch_membership_overview())
    for membership in courses[: max(1, course_limit)]:
        page = fetch_course_assignments(client, membership.url)
        for group in page.exercises:
            for assignment in group.assignments:
                deadlines.append(
                    IliasAssignmentDeadline(
                        course_title=membership.title,
                        course_url=membership.url,
                        exercise_title=group.exercise.label,
                        exercise_url=group.exercise.url,
                        assignment=assignment,
                    )
                )
                if len(deadlines) >= max(1, assignment_limit):
                    return tuple(deadlines)
    return tuple(deadlines)


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


def _course_memberships(items: tuple[IliasMembershipItem, ...]) -> tuple[IliasMembershipItem, ...]:
    return tuple(item for item in items if _is_course_membership(item))


def _is_course_membership(item: IliasMembershipItem) -> bool:
    kind = (item.kind or "").strip().casefold()
    if kind:
        return kind in COURSE_KINDS

    parsed = urlparse(item.url)
    path = parsed.path.casefold()
    return "/goto.php/crs/" in path or path.endswith("/goto.php/crs")
