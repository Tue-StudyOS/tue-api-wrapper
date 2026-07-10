from __future__ import annotations

import hashlib
from typing import Iterable

from .alma_course_search_models import AlmaCourseSearchResult
from .alma_feature_models import AlmaCurrentLecture
from .models import AlmaModuleSearchResult, IliasMembershipItem
from .moodle_models import MoodleCourseSummary
from .course_discovery_models import CourseDiscoveryDocument


def alma_module_documents(items: Iterable[AlmaModuleSearchResult]) -> tuple[CourseDiscoveryDocument, ...]:
    return tuple(
        CourseDiscoveryDocument(
            id=_stable_id("alma-module", item.detail_url or item.number or item.title),
            source="alma",
            kind="module",
            title=item.title,
            text=_join(item.title, item.number, item.element_type),
                url=item.detail_url,
                module_code=item.number,
                module_categories=(),
                degrees=(),
                tags=_clean_tuple((item.element_type,)),
            metadata={"elementType": item.element_type},
        )
        for item in items
    )


def alma_course_documents(items: Iterable[AlmaCourseSearchResult]) -> tuple[CourseDiscoveryDocument, ...]:
    documents: list[CourseDiscoveryDocument] = []
    for item in items:
        instructors = _clean_tuple((item.responsible_lecturer, item.lecturer))
        documents.append(
            CourseDiscoveryDocument(
                id=_stable_id("alma-course", item.detail_url or item.number or item.title),
                source="alma",
                kind="course",
                title=item.title,
                text=_join(item.title, item.number, item.event_type, item.organization, *instructors),
                url=item.detail_url,
                module_code=item.number,
                module_categories=(),
                degrees=(),
                instructors=instructors,
                tags=_clean_tuple((item.event_type, item.organization)),
                metadata={"eventType": item.event_type, "organization": item.organization},
            )
        )
    return tuple(documents)


def alma_current_lecture_documents(items: Iterable[AlmaCurrentLecture]) -> tuple[CourseDiscoveryDocument, ...]:
    documents: list[CourseDiscoveryDocument] = []
    for item in items:
        instructors = _clean_tuple((item.responsible_lecturer, item.lecturer))
        documents.append(
            CourseDiscoveryDocument(
                id=_stable_id("alma-current", item.detail_url or item.number or item.title),
                source="alma",
                kind="lecture",
                title=item.title,
                text=_join(item.title, item.number, item.event_type, item.semester, item.room, *instructors),
                url=item.detail_url,
                module_code=item.number,
                term=item.semester,
                module_categories=(),
                degrees=(),
                instructors=instructors,
                tags=_clean_tuple((item.event_type, item.building, item.room)),
                metadata={"start": item.start, "end": item.end, "room": item.room},
            )
        )
    return tuple(documents)


def ilias_membership_documents(items: Iterable[IliasMembershipItem]) -> tuple[CourseDiscoveryDocument, ...]:
    return tuple(
        CourseDiscoveryDocument(
            id=_stable_id("ilias", item.url or item.info_url or item.title),
            source="ilias",
            kind=item.kind.lower() if item.kind else "course",
            title=item.title,
            text=_join(item.title, item.kind, item.description, *item.properties),
            url=item.url,
            module_categories=(),
            degrees=(),
            tags=_clean_tuple((item.kind, *item.properties)),
            metadata={"infoUrl": item.info_url, "properties": item.properties},
        )
        for item in items
    )


def moodle_course_documents(items: Iterable[MoodleCourseSummary]) -> tuple[CourseDiscoveryDocument, ...]:
    documents: list[CourseDiscoveryDocument] = []
    for item in items:
        documents.append(
            CourseDiscoveryDocument(
                id=_stable_id("moodle", str(item.id) if item.id is not None else item.title),
                source="moodle",
                kind="course",
                title=item.title,
                text=_join(item.title, item.shortname, item.category_name, item.summary, *item.teachers),
                url=item.url,
                module_code=item.shortname,
                module_categories=(),
                degrees=(),
                instructors=item.teachers,
                tags=_clean_tuple((item.category_name, "visible" if item.visible else None)),
                metadata={"id": item.id, "categoryName": item.category_name, "endDate": item.end_date},
            )
        )
    return tuple(documents)


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    return f"{prefix}:{digest}"


def _join(*values: str | None) -> str:
    return " ".join(value.strip() for value in values if value and value.strip())


def _clean_tuple(values: Iterable[str | None]) -> tuple[str, ...]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = value.strip()
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            cleaned.append(normalized)
    return tuple(cleaned)
