from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CourseDiscoveryDocument:
    id: str
    source: str
    kind: str
    title: str
    text: str
    url: str | None = None
    module_code: str | None = None
    degree: str | None = None
    module_categories: tuple[str, ...] = ()
    degrees: tuple[str, ...] = ()
    term: str | None = None
    instructors: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CourseDiscoveryFilters:
    sources: tuple[str, ...] = ()
    kinds: tuple[str, ...] = ()
    degrees: tuple[str, ...] = ()
    module_codes: tuple[str, ...] = ()
    degree: str | None = None
    module_code: str | None = None
    term: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CourseDiscoveryResult:
    document: CourseDiscoveryDocument
    score: float
    match_reason: str


@dataclass(frozen=True)
class CourseDiscoveryFacetOption:
    value: str
    label: str
    count: int


@dataclass(frozen=True)
class CourseDiscoveryFacets:
    sources: tuple[CourseDiscoveryFacetOption, ...] = ()
    kinds: tuple[CourseDiscoveryFacetOption, ...] = ()
    module_codes: tuple[CourseDiscoveryFacetOption, ...] = ()
    degrees: tuple[CourseDiscoveryFacetOption, ...] = ()
    tags: tuple[CourseDiscoveryFacetOption, ...] = ()


@dataclass(frozen=True)
class CourseDiscoveryStatus:
    document_count: int
    semantic_available: bool
    vector_store: str
    embedding_model: str | None
    last_refresh: str | None
    facets: CourseDiscoveryFacets = field(default_factory=CourseDiscoveryFacets)
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class CourseDiscoverySearchResponse:
    query: str
    results: tuple[CourseDiscoveryResult, ...]
    status: CourseDiscoveryStatus
    errors: tuple[str, ...] = ()
