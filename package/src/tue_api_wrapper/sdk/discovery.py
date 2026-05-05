from __future__ import annotations

from dataclasses import dataclass, field

from ..course_discovery_models import CourseDiscoveryFilters
from ..course_discovery_service import CourseDiscoveryService


@dataclass(slots=True)
class CourseDiscoveryApi:
    service: CourseDiscoveryService = field(default_factory=CourseDiscoveryService)

    def search(
        self,
        query: str,
        *,
        sources: tuple[str, ...] = (),
        kinds: tuple[str, ...] = (),
        degrees: tuple[str, ...] = (),
        module_codes: tuple[str, ...] = (),
        degree: str | None = None,
        module_code: str | None = None,
        term: str | None = None,
        tags: tuple[str, ...] = (),
        include_private: bool = True,
        limit: int = 20,
    ):
        return self.service.search(
            query,
            filters=CourseDiscoveryFilters(
                sources=sources,
                kinds=kinds,
                degrees=degrees,
                module_codes=module_codes,
                degree=degree,
                module_code=module_code,
                term=term,
                tags=tags,
            ),
            include_private=include_private,
            limit=limit,
        )

    def refresh(self, *, query: str = "", include_private: bool = True, limit: int = 3000):
        return self.service.refresh(query=query, include_private=include_private, limit=limit)

    def status(self):
        return self.service.status()
