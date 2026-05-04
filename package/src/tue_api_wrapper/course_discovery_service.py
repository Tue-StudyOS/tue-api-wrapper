from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .alma_course_search_client import search_courses
from .alma_feature_client import fetch_current_lectures
from .client import AlmaClient
from .config import AlmaError
from .course_discovery_cache import CourseDiscoveryCache
from .course_discovery_detail import enrich_with_alma_detail
from .course_discovery_embeddings import build_embedding_provider
from .course_discovery_lance import build_lance_store
from .course_discovery_models import (
    CourseDiscoveryDocument,
    CourseDiscoveryFilters,
    CourseDiscoverySearchResponse,
    CourseDiscoveryStatus,
)
from .course_discovery_facets import build_facets, metadata_values
from .course_discovery_sources import (
    alma_course_documents,
    alma_current_lecture_documents,
    alma_module_documents,
    ilias_membership_documents,
    moodle_course_documents,
)
from .course_discovery_program_search import fetch_program_scoped_documents
from .course_discovery_store import InMemoryDiscoveryStore
from .ilias_client import IliasClient
from .moodle_auth import build_moodle_client

AlmaLoader = Callable[[], AlmaClient]
IliasLoader = Callable[[], IliasClient]


class CourseDiscoveryService:
    def __init__(
        self,
        *,
        public_alma: AlmaClient | None = None,
        alma_loader: AlmaLoader | None = None,
        ilias_loader: IliasLoader | None = None,
    ) -> None:
        self._public_alma = public_alma or AlmaClient()
        self._alma_loader = alma_loader
        self._ilias_loader = ilias_loader
        self._embedding_provider = build_embedding_provider()
        self._store = build_lance_store(self._embedding_provider) or InMemoryDiscoveryStore()
        self._store_name = getattr(self._store, "name", "memory")
        self._cache = CourseDiscoveryCache()
        self._last_refresh: str | None = None
        self._errors: list[str] = []
        self._available_degree_labels: tuple[str, ...] = ()
        cached_documents, self._last_refresh = self._cache.load()
        if cached_documents:
            self._store.replace(cached_documents)

    def refresh(
        self,
        *,
        query: str = "",
        include_private: bool = False,
        limit: int = 1200,
    ) -> CourseDiscoveryStatus:
        documents, errors = self._collect_documents(query=query, include_private=include_private, limit=limit, sync_all=True)
        documents = _dedupe_documents(documents)[:limit]
        documents = self._enrich_alma_details(documents, errors)
        self._last_refresh = datetime.now(timezone.utc).isoformat()
        self._cache.save(documents, self._last_refresh)
        self._store.replace(documents)
        self._errors = list(errors)
        return self.status()

    def search(
        self,
        query: str,
        *,
        filters: CourseDiscoveryFilters | None = None,
        include_private: bool = False,
        limit: int = 20,
    ) -> CourseDiscoverySearchResponse:
        filters = filters or CourseDiscoveryFilters()
        errors: tuple[str, ...] = ()
        if not self._store.documents():
            documents, errors = self._collect_documents(query=query, include_private=include_private, limit=max(limit * 3, 30))
            self._store.replace(_dedupe_documents(documents))
        results = self._store.search(query, filters, limit)
        if filters.degrees and not results:
            scoped_documents, scoped_errors = fetch_program_scoped_documents(
                self._public_alma,
                query=query,
                labels=filters.degrees,
                limit=max(limit * 3, 30),
            )
            errors = (*errors, *scoped_errors)
            if scoped_documents:
                self._store.add(_dedupe_documents(scoped_documents))
                results = self._store.search(query, filters, limit)
        return CourseDiscoverySearchResponse(query=query, results=results, status=self.status(), errors=errors)

    def status(self) -> CourseDiscoveryStatus:
        return CourseDiscoveryStatus(
            document_count=len(self._store.documents()),
            semantic_available=self._embedding_provider.model_name is not None and self._store_name == "lancedb",
            vector_store=self._store_name,
            embedding_model=self._embedding_provider.model_name,
            last_refresh=self._last_refresh,
            facets=build_facets(self._store.documents(), extra_degrees=self._degree_labels()),
            errors=tuple(self._errors),
        )

    def _collect_documents(
        self,
        *,
        query: str,
        include_private: bool,
        limit: int,
        sync_all: bool = False,
    ):
        documents = []
        errors: list[str] = []
        documents.extend(self._public_alma_documents(query=query, limit=limit, sync_all=sync_all, errors=errors))

        if include_private:
            documents.extend(self._private_documents(query=query, limit=limit, errors=errors))
        return tuple(documents), tuple(errors)

    def _public_alma_documents(self, *, query: str, limit: int, sync_all: bool, errors: list[str]):
        if not sync_all:
            try:
                modules = self._public_alma.search_public_module_descriptions(query=query, max_results=limit)
                return list(alma_module_documents(modules.results))
            except AlmaError as error:
                errors.append(f"Alma module search failed: {error}")
                return []

        documents = []
        try:
            filters = self._public_alma.fetch_public_module_search_filters()
            self._available_degree_labels = _option_labels(filters.subjects)
            for option in filters.subjects:
                if len(documents) >= limit:
                    break
                modules = self._public_alma.search_public_module_descriptions(subjects=(option.value,), max_results=300)
                documents.extend(_annotate_documents(alma_module_documents(modules.results), degree=option.label))
            for option in filters.degrees:
                if len(documents) >= limit:
                    break
                modules = self._public_alma.search_public_module_descriptions(degrees=(option.value,), max_results=200)
                documents.extend(_annotate_documents(alma_module_documents(modules.results), tag=option.label))
            for option in filters.subjects:
                if len(documents) >= limit:
                    break
                modules = self._public_alma.search_public_module_descriptions(subjects=(option.value,), max_results=300)
                documents.extend(_annotate_documents(alma_module_documents(modules.results), tag=option.label))
        except AlmaError as error:
            errors.append(f"Alma corpus sync failed: {error}")
        return documents

    def _degree_labels(self) -> tuple[str, ...]:
        if self._available_degree_labels:
            return self._available_degree_labels
        try:
            filters = self._public_alma.fetch_public_module_search_filters()
        except AlmaError:
            return ()
        self._available_degree_labels = _option_labels(filters.subjects)
        return self._available_degree_labels

    def _private_documents(self, *, query: str, limit: int, errors: list[str]):
        documents = []
        if self._alma_loader is not None:
            try:
                alma = self._alma_loader()
                documents.extend(alma_course_documents(search_courses(alma, query=query, limit=limit).results))
                documents.extend(alma_current_lecture_documents(fetch_current_lectures(alma, limit=min(limit, 50)).results))
            except AlmaError as error:
                errors.append(f"Authenticated Alma discovery failed: {error}")

        if self._ilias_loader is not None:
            try:
                documents.extend(ilias_membership_documents(self._ilias_loader().fetch_membership_overview()))
            except AlmaError as error:
                errors.append(f"ILIAS discovery failed: {error}")

        try:
            documents.extend(moodle_course_documents(build_moodle_client().fetch_enrolled_courses(limit=limit).items))
        except AlmaError as error:
            errors.append(f"Moodle discovery failed: {error}")
        return documents

    def _enrich_alma_details(
        self,
        documents: tuple[CourseDiscoveryDocument, ...],
        errors: list[str],
    ) -> tuple[CourseDiscoveryDocument, ...]:
        enriched: list[CourseDiscoveryDocument] = []
        failures = 0
        for document in documents:
            if document.source != "alma" or not document.url:
                enriched.append(document)
                continue
            try:
                detail = self._public_alma.fetch_public_module_detail(document.url)
                enriched.append(enrich_with_alma_detail(document, detail))
            except AlmaError:
                failures += 1
                enriched.append(document)
        if failures:
            errors.append(f"Alma detail enrichment failed for {failures} indexed items.")
        return tuple(enriched)


def _dedupe_documents(documents) -> tuple[CourseDiscoveryDocument, ...]:
    merged: dict[str, CourseDiscoveryDocument] = {}
    for document in documents:
        existing = merged.get(document.id)
        if existing is None:
            merged[document.id] = document
            continue
        degrees = metadata_values(existing.metadata, "degrees")
        if existing.degree:
            degrees.add(existing.degree)
        if document.degree:
            degrees.add(document.degree)
        merged[document.id] = CourseDiscoveryDocument(
            id=existing.id,
            source=existing.source,
            kind=existing.kind,
            title=existing.title,
            text=existing.text,
            url=existing.url,
            module_code=existing.module_code,
            degree=existing.degree or document.degree,
            term=existing.term or document.term,
            instructors=_merge_tuple(existing.instructors, document.instructors),
            module_categories=_merge_tuple(existing.module_categories, document.module_categories),
            degrees=_merge_tuple(existing.degrees, document.degrees),
            tags=_merge_tuple(existing.tags, document.tags),
            metadata={**existing.metadata, **document.metadata, "degrees": tuple(sorted(degrees))},
        )
    return tuple(merged.values())


def _annotate_documents(
    documents: tuple[CourseDiscoveryDocument, ...],
    *,
    degree: str | None = None,
    tag: str | None = None,
) -> tuple[CourseDiscoveryDocument, ...]:
    annotated = []
    for document in documents:
        tags = document.tags
        metadata = dict(document.metadata)
        if degree:
            tags = _merge_tuple(tags, (degree,))
            metadata["degrees"] = _merge_tuple(tuple(metadata.get("degrees", ())), (degree,))
        if tag:
            tags = _merge_tuple(tags, (tag,))
        annotated.append(
            CourseDiscoveryDocument(
                id=document.id,
                source=document.source,
                kind=document.kind,
                title=document.title,
                text=document.text,
                url=document.url,
                module_code=document.module_code,
                degree=degree or document.degree,
                term=document.term,
                instructors=document.instructors,
                module_categories=document.module_categories,
                degrees=_merge_tuple(document.degrees, (degree,) if degree else ()),
                tags=tags,
                metadata=metadata,
            )
        )
    return tuple(annotated)


def _option_labels(options) -> tuple[str, ...]:
    return tuple(option.label for option in options if option.label and option.value != "ISNULL")


def _merge_tuple(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in (*left, *right):
        key = value.lower()
        if key not in seen:
            seen.add(key)
            merged.append(value)
    return tuple(merged)
