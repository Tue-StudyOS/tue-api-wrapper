from __future__ import annotations

import argparse
from collections.abc import Collection
from pathlib import Path
from typing import Any

from .course_discovery_models import CourseDiscoveryFilters
from .course_discovery_service import CourseDiscoveryService
from .portal_common import serialize
from .sdk import (
    TuebingenAuthenticatedClient,
    TuebingenPublicClient,
    UniversityCredentials,
)

MCP_SERVICES = frozenset({"public", "discovery", "alma", "ilias", "moodle", "mail"})


def create_mcp_server(
    *,
    env_file: str | Path | None = ".env",
    host: str = "127.0.0.1",
    port: int = 8765,
    services: Collection[str] | None = None,
):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:  # pragma: no cover - depends on optional install extras
        raise RuntimeError("Install MCP support with: pip install -e '.[mcp]'") from error

    enabled_services = _enabled_services(services)
    server = FastMCP(
        "tue-api-wrapper",
        instructions=(
            "University of Tübingen data tools. Public tools do not need credentials. "
            "Authenticated tools read UNI_USERNAME and UNI_PASSWORD from the environment or .env."
        ),
        host=host,
        port=port,
    )

    if "public" in enabled_services:
        _register_public_tools(server, TuebingenPublicClient())
    if "discovery" in enabled_services:
        _register_discovery_tools(server, env_file)
    if "alma" in enabled_services:
        _register_alma_tools(server, env_file)
    if "ilias" in enabled_services:
        _register_ilias_tools(server, env_file)
    if "moodle" in enabled_services:
        _register_moodle_tools(server, env_file)
    if "mail" in enabled_services:
        _register_mail_tools(server, env_file)

    return server


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    server = create_mcp_server(env_file=args.env_file, host=args.host, port=args.port, services=args.services)
    server.run(args.transport)


def _enabled_services(services: Collection[str] | None) -> frozenset[str]:
    if services is None:
        return MCP_SERVICES
    unknown = set(services) - MCP_SERVICES
    if unknown:
        raise ValueError(f"Unknown MCP service: {', '.join(sorted(unknown))}")
    return frozenset(services)


def _register_public_tools(server: Any, client: TuebingenPublicClient) -> None:
    @server.tool()
    def public_alma_search_modules(query: str, max_results: int = 10) -> dict[str, Any]:
        """Search public Alma module descriptions."""
        return _serialized(client.alma.search_modules(query, max_results=max_results))

    @server.tool()
    def public_alma_current_lectures(date: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Load public Alma current lectures for a date such as 02.05.2026."""
        return _serialized(client.alma.current_lectures(date=date, limit=limit))

    @server.tool()
    def public_campus_events(query: str = "", limit: int = 12) -> dict[str, Any]:
        """Search public University of Tübingen event calendar entries."""
        return _serialized(client.campus.events(query=query, limit=limit))

    @server.tool()
    def public_campus_canteens(menu_date: str | None = None) -> dict[str, Any]:
        """Load public canteen menu data for Tübingen canteens."""
        return _serialized(client.campus.canteens(menu_date=menu_date))

    @server.tool()
    def public_campus_seat_availability() -> dict[str, Any]:
        """Load public University Library seat availability from the Tübingen seatfinder."""
        return _serialized(client.campus.seat_availability())

    @server.tool()
    def public_timms_search(query: str, limit: int = 10) -> dict[str, Any]:
        """Search public TIMMS lecture recordings."""
        return _serialized(client.timms.search(query, limit=limit))


def _register_discovery_tools(server: Any, env_file: str | Path | None) -> None:
    discovery = CourseDiscoveryService(
        alma_loader=lambda: _authenticated(env_file).alma.client,
        ilias_loader=lambda: _authenticated(env_file).ilias.client,
    )

    @server.tool()
    def course_discovery_search(
        query: str,
        source: str = "",
        kind: str = "",
        degree: str = "",
        module_code: str = "",
        include_private: bool = True,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search Alma modules and optional local authenticated course sources."""
        filters = CourseDiscoveryFilters(
            sources=_csv(source),
            kinds=_csv(kind),
            degrees=_csv_preserve(degree),
            module_codes=_csv_preserve(module_code),
        )
        return _serialized(discovery.search(query, filters=filters, include_private=include_private, limit=limit))

    @server.tool()
    def course_discovery_status() -> dict[str, Any]:
        """Show local course discovery index and semantic search availability."""
        return _serialized(discovery.status())

    @server.tool()
    def course_discovery_refresh(include_private: bool = True, limit: int = 3000) -> dict[str, Any]:
        """Sync Alma, ILIAS, and Moodle course data into the local discovery index."""
        return _serialized(discovery.refresh(include_private=include_private, limit=limit))


def _register_alma_tools(server: Any, env_file: str | Path | None) -> None:
    @server.tool()
    def authenticated_alma_timetable(term: str) -> dict[str, Any]:
        """Load the authenticated Alma timetable for a term such as Sommer 2026."""
        return _serialized(_authenticated(env_file).alma.timetable(term))


def _register_ilias_tools(server: Any, env_file: str | Path | None) -> None:
    @server.tool()
    def authenticated_ilias_tasks() -> dict[str, Any]:
        """Load authenticated ILIAS task overview data."""
        return _serialized(_authenticated(env_file).ilias.tasks())


def _register_moodle_tools(server: Any, env_file: str | Path | None) -> None:
    @server.tool()
    def authenticated_moodle_deadlines(days: int = 30, limit: int = 50) -> dict[str, Any]:
        """Load authenticated Moodle calendar deadlines."""
        return _serialized(_authenticated(env_file).moodle.deadlines(days=days, limit=limit))


def _register_mail_tools(server: Any, env_file: str | Path | None) -> None:
    @server.tool()
    def authenticated_mail_inbox(limit: int = 10) -> dict[str, Any]:
        """Load an authenticated read-only university mail inbox summary."""
        client = _authenticated(env_file)
        try:
            return _serialized(client.mail.inbox(limit=limit))
        finally:
            client.close()


def _authenticated(env_file: str | Path | None) -> TuebingenAuthenticatedClient:
    return TuebingenAuthenticatedClient(UniversityCredentials.from_env(env_file))


def _serialized(value: object) -> dict[str, Any]:
    payload = serialize(value)
    return payload if isinstance(payload, dict) else {"items": payload}


def _csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip().lower() for part in value.split(",") if part.strip())


def _csv_preserve(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local Tübingen study data MCP server.")
    parser.add_argument("--env-file", default=".env", help="Path to a .env file with UNI_USERNAME and UNI_PASSWORD.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default="stdio",
        help="MCP transport. Use stdio for most local agent clients.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP-based MCP transports.")
    parser.add_argument("--port", default=8765, type=int, help="Port for HTTP-based MCP transports.")
    parser.add_argument(
        "--service",
        dest="services",
        action="append",
        choices=sorted(MCP_SERVICES),
        help="Expose only this service's tools. Repeat to enable multiple services; omit for all services.",
    )
    return parser


if __name__ == "__main__":
    main()
