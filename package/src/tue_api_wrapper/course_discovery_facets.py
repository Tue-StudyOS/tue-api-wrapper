from __future__ import annotations

import re

from .course_discovery_models import CourseDiscoveryDocument, CourseDiscoveryFacetOption, CourseDiscoveryFacets

CODE_PREFIX_RE = re.compile(r"^[A-ZÄÖÜ]{2,}(?:-[A-ZÄÖÜ]+)?")
NOISY_TAG_PREFIXES = (
    "anmeldungs",
    "veranstaltungszeitraum:",
)
NOISY_TAG_VALUES = {
    "(nicht gefüllt)",
    "prüfung",
    "studienleistung",
    "veranstaltung",
    "modul",
    "kurs",
    "visible",
}


def build_facets(
    documents: tuple[CourseDiscoveryDocument, ...],
    *,
    extra_degrees: tuple[str, ...] = (),
) -> CourseDiscoveryFacets:
    return CourseDiscoveryFacets(
        sources=_facet(document.source for document in documents),
        kinds=_facet(document.kind for document in documents),
        module_codes=_facet(_document_module_codes(documents), limit=1000),
        degrees=_facet((*_document_degrees(documents), *extra_degrees), limit=1000),
        tags=_facet(_meaningful_tags(documents), limit=300),
    )


def metadata_values(metadata: dict[str, object], key: str) -> set[str]:
    values = metadata.get(key)
    if isinstance(values, (list, tuple)):
        return {str(value) for value in values if value}
    return set()


def _document_module_codes(documents: tuple[CourseDiscoveryDocument, ...]):
    for document in documents:
        yield from document.module_categories
        if document.module_code:
            match = CODE_PREFIX_RE.match(document.module_code.strip())
            if match:
                yield match.group(0)


def _document_degrees(documents: tuple[CourseDiscoveryDocument, ...]):
    for document in documents:
        if document.degree:
            yield document.degree
        yield from document.degrees
        yield from metadata_values(document.metadata, "degrees")
        yield from metadata_values(document.metadata, "studyPrograms")


def _meaningful_tags(documents: tuple[CourseDiscoveryDocument, ...]):
    for document in documents:
        for tag in document.tags:
            normalized = tag.strip().casefold()
            if not normalized or normalized in NOISY_TAG_VALUES:
                continue
            if any(normalized.startswith(prefix) for prefix in NOISY_TAG_PREFIXES):
                continue
            yield tag


def _facet(values, *, limit: int = 120) -> tuple[CourseDiscoveryFacetOption, ...]:
    counts: dict[str, int] = {}
    for value in values:
        normalized = str(value).strip()
        if normalized:
            counts[normalized] = counts.get(normalized, 0) + 1
    return tuple(
        CourseDiscoveryFacetOption(value=value, label=value, count=count)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))[:limit]
    )
