"""Search existing source clients independently; never merge course identities."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .portal_common import serialize


def search_courses_live(client: Any, query: str, *, term: str | None = None,
                        limit: int = 20, moodle_offset: int = 0) -> dict[str, Any]:
    query = query.strip()
    if not query or not 1 <= limit <= 100 or moodle_offset < 0 or moodle_offset % limit:
        raise ValueError("A query, limit 1–100 and Moodle offset divisible by limit are required")
    sources: dict[str, Any] = {}

    def alma():
        page = client.alma.course_offerings(query=query, term=term, limit=limit)
        return {"items": serialize(page.results), "selected_term": page.selected_term_label,
                "coverage": "bounded; Alma search term only"}

    def ilias():
        page = client.ilias.search(query, page=1)
        return {"items": serialize(page.results[:limit]), "has_next_page": bool(page.next_page_url),
                "truncated": len(page.results) > limit, "coverage": "first search page; term not filtered"}

    def moodle():
        page = client.moodle.search_courses(query, page=moodle_offset // limit, per_page=limit)
        return {"items": serialize(page.items), "scope": "visible_catalogue", "source_url": page.source_url,
                "next_offset": page.next_page * limit if page.next_page is not None else None,
                "coverage": "one catalogue search page; term not filtered"}

    for name, operation in (("alma", alma), ("ilias", ilias), ("moodle", moodle)):
        try:
            sources[name] = {"status": "ok", **operation()}
        except Exception as error:
            sources[name] = {"status": "error", "error": type(error).__name__, "items": []}
    return {"query": query, "observed_at": datetime.now(timezone.utc).isoformat(),
            "matches": "candidates_only", "sources": sources}
