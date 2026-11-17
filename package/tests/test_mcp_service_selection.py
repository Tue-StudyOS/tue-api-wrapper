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
                "public_alma_program_filters",
                "public_alma_search_program",
                "public_alma_current_lectures",
                "public_campus_events",
                "public_campus_canteens",
                "public_campus_seat_availability",
                "public_timms_search",
            },
        ),
        ("discovery", {"course_discovery_search", "course_discovery_status", "course_discovery_refresh"}),
        ("alma", {"authenticated_alma_timetable"}),
        ("ilias", {"authenticated_ilias_tasks", "authenticated_ilias_quiz", "authenticated_ilias_quiz_deadlines"}),
        ("moodle", {"authenticated_moodle_deadlines"}),
        ("mail", {"authenticated_mail_inbox"}),
        ("campus", {"campus_buildings", "campus_people_search", "campus_advising_page", "campus_advising_discover", "campus_advising_refresh", "campus_advising_search", "campus_rooms_search", "campus_fitness_courses", "campus_connectivity"}),
        ("raw", {"raw_course_page", "raw_alma_course_search", "raw_moodle_search", "raw_ilias_search", "raw_interaction_page"}),
        ("forum-write", {"moodle_forum_review", "moodle_forum_publish", "ilias_forum_review", "ilias_forum_publish"}),
        ("quiz-write", {"moodle_quiz_review_start", "moodle_quiz_start", "moodle_quiz_review_answers",
                        "moodle_quiz_save_answers", "moodle_quiz_review_finish", "moodle_quiz_finish",
                        "ilias_quiz_review_start", "ilias_quiz_start", "ilias_quiz_question",
                        "ilias_quiz_review_answers", "ilias_quiz_save_answers", "ilias_quiz_review_finish", "ilias_quiz_finish"}),
    ],
)
def test_create_mcp_server_limits_tools_to_selected_service(service: str, expected_tools: set[str]) -> None:
    server = create_mcp_server(services=(service,))

    assert set(server.tools) == expected_tools


def test_create_mcp_server_rejects_unknown_service() -> None:
    with pytest.raises(ValueError, match="Unknown MCP service"):
        create_mcp_server(services=("everything",))


def test_raw_tools_are_opt_in() -> None:
    assert "raw_course_page" not in create_mcp_server().tools
