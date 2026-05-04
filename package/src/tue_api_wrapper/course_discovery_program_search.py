from __future__ import annotations

from dataclasses import dataclass

from .client import AlmaClient
from .config import AlmaError
from .course_discovery_models import CourseDiscoveryDocument
from .course_discovery_sources import alma_module_documents
from .models import AlmaSearchOption


def fetch_program_scoped_documents(
    alma: AlmaClient,
    *,
    query: str,
    labels: tuple[str, ...],
    limit: int,
) -> tuple[tuple[CourseDiscoveryDocument, ...], tuple[str, ...]]:
    try:
        filters = alma.fetch_public_module_search_filters()
        options = (
            *(_program_option("subject", option) for option in filters.subjects),
            *(_program_option("degree", option) for option in filters.degrees),
        )
        selected = tuple(option for option in options if _label_matches(option.label, labels))
        documents: list[CourseDiscoveryDocument] = []
        for option in selected:
            if len(documents) >= limit:
                break
            response = alma.search_public_module_descriptions(
                query=query,
                subjects=(option.value,) if option.kind == "subject" else (),
                degrees=(option.value,) if option.kind == "degree" else (),
                max_results=min(300, max(limit, 20)),
            )
            documents.extend(_annotate(alma_module_documents(response.results), option.label))
        return tuple(documents[:limit]), ()
    except AlmaError as error:
        return (), (f"Alma program-scoped search failed: {error}",)


def _program_option(kind: str, option: AlmaSearchOption) -> "_ProgramOption":
    return _ProgramOption(kind=kind, value=option.value, label=option.label)


def _label_matches(label: str, selected: tuple[str, ...]) -> bool:
    normalized = label.casefold()
    return any(normalized == value.casefold() for value in selected)


def _annotate(documents: tuple[CourseDiscoveryDocument, ...], degree: str) -> tuple[CourseDiscoveryDocument, ...]:
    annotated: list[CourseDiscoveryDocument] = []
    for document in documents:
        annotated.append(
            CourseDiscoveryDocument(
                id=document.id,
                source=document.source,
                kind=document.kind,
                title=document.title,
                text=document.text,
                url=document.url,
                module_code=document.module_code,
                degree=degree,
                module_categories=document.module_categories,
                degrees=(*document.degrees, degree),
                term=document.term,
                instructors=document.instructors,
                tags=(*document.tags, degree),
                metadata={**document.metadata, "degrees": (*_metadata_tuple(document.metadata.get("degrees")), degree)},
            )
        )
    return tuple(annotated)


def _metadata_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item)
    if value:
        return (str(value),)
    return ()


@dataclass(frozen=True)
class _ProgramOption:
    kind: str
    value: str
    label: str
