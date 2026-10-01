from __future__ import annotations

import sys
from types import ModuleType

import pytest

from tue_api_wrapper.mcp_server import create_mcp_server


class FakeFastMCP:
    def __init__(self, *_args, **_kwargs):
        self.tools: list[str] = []

    def tool(self):
        def register(function):
            self.tools.append(function.__name__)
            return function

        return register


@pytest.fixture(autouse=True)
def fake_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    mcp_module = ModuleType("mcp")
    server_module = ModuleType("mcp.server")
    fastmcp_module = ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = FakeFastMCP
    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)


@pytest.mark.parametrize(
    ("service", "expected_tools"),
    [
        (
            "public",
            {
                "public_alma_search_modules",
                "public_alma_current_lectures",
                "public_campus_events",
                "public_campus_canteens",
                "public_campus_seat_availability",
                "public_timms_search",
            },
        ),
        ("discovery", {"course_discovery_search", "course_discovery_status", "course_discovery_refresh"}),
        ("alma", {"authenticated_alma_timetable"}),
        ("ilias", {"authenticated_ilias_tasks"}),
        ("moodle", {"authenticated_moodle_deadlines"}),
        ("mail", {"authenticated_mail_inbox"}),
    ],
)
def test_create_mcp_server_limits_tools_to_selected_service(service: str, expected_tools: set[str]) -> None:
    server = create_mcp_server(services=(service,))

    assert set(server.tools) == expected_tools


def test_create_mcp_server_rejects_unknown_service() -> None:
    with pytest.raises(ValueError, match="Unknown MCP service"):
        create_mcp_server(services=("everything",))
