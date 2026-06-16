from __future__ import annotations

from dataclasses import dataclass

from .models import IliasContentItem, IliasContentPage, IliasExerciseAssignment


@dataclass(frozen=True)
class IliasCourseExerciseAssignments:
    exercise: IliasContentItem
    assignments: tuple[IliasExerciseAssignment, ...]


@dataclass(frozen=True)
class IliasCourseAssignmentsPage:
    course: IliasContentPage
    exercises: tuple[IliasCourseExerciseAssignments, ...]
