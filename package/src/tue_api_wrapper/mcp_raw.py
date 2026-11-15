from __future__ import annotations

from pathlib import Path
from typing import Any

from .raw_course_response import get_raw_course_response
from .study_radar_runtime import make_client
from .alma_course_search_raw import fetch_raw_alma_search
from .moodle_course_search import raw_moodle_course_search
from .ilias_search_raw import fetch_raw_ilias_search
from .raw_interactions import raw_interaction


def register_raw_tools(server: Any, env_file: str | Path | None) -> None:
    @server.tool()
    def raw_interaction_page(service: str, kind: str, target: str, page: int = 0) -> dict[str, Any]:
        """Read unredacted forum, quiz or attempt HTML; it can contain private data and session tokens."""
        client, _ = make_client(env_file)
        try:
            return raw_interaction(client, service, kind, target, page=page)
        finally:
            client.close()

    @server.tool()
    def raw_ilias_search(query: str = "", form_only: bool = False) -> dict[str, Any]:
        """Read unredacted ILIAS search form or first results page. HTML may contain private data and session tokens."""
        client, _ = make_client(env_file)
        try:
            return fetch_raw_ilias_search(client.ilias.client, query=query, form_only=form_only)
        finally:
            client.close()

    @server.tool()
    def raw_moodle_search(query: str, page: int = 0, per_page: int = 20) -> dict[str, Any]:
        """Return unredacted Moodle catalogue search HTML, which may contain session tokens or private data."""
        client, _ = make_client(env_file)
        try:
            return raw_moodle_course_search(client.moodle.client, query, page=page, per_page=per_page)
        finally:
            client.close()

    @server.tool()
    def raw_alma_course_search(query: str = "", term: str | None = None, form_only: bool = False) -> dict[str, Any]:
        """Return unredacted Alma search form or results HTML; it may contain private data or active session tokens."""
        client, _ = make_client(env_file)
        try:
            return fetch_raw_alma_search(client.alma.client, query=query, term=term, form_only=form_only)
        finally:
            client.close()

    @server.tool()
    def raw_course_page(service: str, course_id: str) -> dict[str, Any]:
        """Explicitly read unredacted Moodle or ILIAS course HTML; it may contain private data and session tokens. Redirects are not followed."""
        client, _ = make_client(env_file)
        try:
            return get_raw_course_response(client, service, course_id)
        finally:
            client.close()
