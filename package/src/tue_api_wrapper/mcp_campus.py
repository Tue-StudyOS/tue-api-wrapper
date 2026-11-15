from __future__ import annotations

from typing import Any

from .portal_common import serialize
from .sdk import TuebingenPublicClient
from .connectivity import check_connectivity


def register_campus_tools(server: Any) -> None:
    client = TuebingenPublicClient()

    @server.tool()
    def campus_connectivity() -> dict[str, Any]:
        """Check eduVPN status where supported and reachability of Alma, ILIAS and Moodle without logging in."""
        return check_connectivity()

    @server.tool()
    def campus_buildings() -> dict[str, Any]:
        """Read the university's public building directory."""
        return serialize(client.campus.buildings())

    @server.tool()
    def campus_people_search(query: str) -> dict[str, Any]:
        """Search the university's public people directory."""
        value = serialize(client.directory.search(query))
        return value if isinstance(value, dict) else {"items": value}

    @server.tool()
    def campus_rooms_search(query: str = "", page: int = 1, page_size: int = 25) -> dict[str, Any]:
        """Search public anny resources; availability does not make a reservation."""
        return serialize(client.anny.resources(query=query, page=page, page_size=page_size))

    @server.tool()
    def campus_fitness_courses(query: str = "", limit: int = 50) -> dict[str, Any]:
        """Search public university sports courses."""
        value = serialize(client.campus.fitness_courses(query=query, limit=limit))
        return value if isinstance(value, dict) else {"items": value}
