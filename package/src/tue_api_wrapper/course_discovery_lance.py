from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from .course_discovery_embeddings import EmbeddingProvider
from .course_discovery_models import CourseDiscoveryDocument, CourseDiscoveryFilters, CourseDiscoveryResult
from .course_discovery_store import InMemoryDiscoveryStore


class LanceDiscoveryStore:
    def __init__(self, provider: EmbeddingProvider, path: str | None = None) -> None:
        import lancedb

        self._provider = provider
        self._path = Path(path or os.getenv("TUE_DISCOVERY_DB", "~/.tue-api-wrapper/course-discovery")).expanduser()
        self._db = lancedb.connect(str(self._path))
        self._table = None
        self._lexical = InMemoryDiscoveryStore()

    @property
    def name(self) -> str:
        return "lancedb"

    def replace(self, documents: tuple[CourseDiscoveryDocument, ...]) -> None:
        rows = self._rows(documents)
        self._lexical.replace(documents)
        if not rows:
            self._table = None
            return
        self._table = self._db.create_table("courses", data=rows, mode="overwrite")

    def add(self, documents: tuple[CourseDiscoveryDocument, ...]) -> None:
        if self._table is None:
            self.replace(documents)
            return
        self.replace((*self._lexical.documents(), *documents))

    def documents(self) -> tuple[CourseDiscoveryDocument, ...]:
        return self._lexical.documents()

    def search(self, query: str, filters: CourseDiscoveryFilters, limit: int) -> tuple[CourseDiscoveryResult, ...]:
        if self._table is None or not query.strip():
            return self._lexical.search(query, filters, limit)
        vector = self._provider.embed((query,))[0]
        rows = self._table.search(vector).limit(max(limit * 4, limit)).to_list()
        documents = {document.id: document for document in self._lexical.documents()}
        results: list[CourseDiscoveryResult] = []
        seen_ids: set[str] = set()
        for row in rows:
            document = documents.get(str(row["id"]))
            if document is None or document.id in seen_ids or not _matches(document, filters):
                continue
            seen_ids.add(document.id)
            distance = float(row.get("_distance", 0.0))
            results.append(CourseDiscoveryResult(document, _distance_to_similarity(distance), "Semantic vector match"))
            if len(results) >= limit:
                break
        return tuple(results) or self._lexical.search(query, filters, limit)

    def _rows(self, documents: tuple[CourseDiscoveryDocument, ...]) -> list[dict[str, object]]:
        vectors = self._provider.embed(tuple(_embedding_text(document) for document in documents))
        return [
            {"id": document.id, "vector": vector, "payload": asdict(document)}
            for document, vector in zip(documents, vectors, strict=True)
        ]


def build_lance_store(provider: EmbeddingProvider) -> LanceDiscoveryStore | None:
    if os.getenv("TUE_DISCOVERY_VECTOR_STORE", "").strip().lower() != "lancedb":
        return None
    if provider.model_name is None:
        return None
    try:
        return LanceDiscoveryStore(provider)
    except ImportError:
        return None


def _embedding_text(document: CourseDiscoveryDocument) -> str:
    return " ".join((document.title, document.text, " ".join(document.tags)))


def _matches(document: CourseDiscoveryDocument, filters: CourseDiscoveryFilters) -> bool:
    temporary = InMemoryDiscoveryStore()
    temporary.replace((document,))
    return bool(temporary.search("", filters, 1))


def _distance_to_similarity(distance: float) -> float:
    # LanceDB reports squared L2 distance for normalized vectors by default.
    return max(0.0, min(1.0, 1.0 - (distance / 2.0)))
