"""Single command-line entry point for the university clients and local servers."""
from __future__ import annotations

import argparse
import sys
from importlib import import_module
from collections.abc import Sequence

COMMANDS = {
    "study": ("study_radar_cli", "Read university data and study observations"),
    "timetable": ("cli", "Read an Alma timetable"),
    "academics": ("alma_academics_cli", "Read Alma academic data"),
    "document": ("alma_documents_cli", "Read Alma documents"),
    "ilias-content": ("ilias_content_cli", "Read ILIAS content"),
    "ilias-learning": ("ilias_learning_cli", "Read ILIAS learning data"),
    "ilias-root": ("ilias_cli", "Read the ILIAS root"),
    "route-discovery": ("route_discovery_cli", "Inspect university request routes"),
    "register": ("registration_cli", "Review and manage registrations"),
    "submit": ("moodle_submission_cli", "Review and submit Moodle work"),
    "forum": ("moodle_forum_cli", "Review and manage forum posts"),
    "quiz": ("moodle_quiz_cli", "Review and manage quiz attempts"),
    "mcp": ("mcp_server", "Start the local MCP server"),
    "api-server": ("api_server", "Start the local HTTP API"),
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tue", description=__doc__)
    parser.epilog = "Commands:\n" + "\n".join(
        f"  {name:16} {description}" for name, (_, description) in COMMANDS.items()
    )
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument("command", choices=COMMANDS, help="Operation to run")
    arguments = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(arguments[:1])
    remaining = arguments[1:]
    if args.command == "api-server" and remaining == ["--help"]:
        print("usage: tue api-server\n\nStart the local HTTP API. Configure HOST and PORT via the environment.")
        return 0
    module = import_module(f".{COMMANDS[args.command][0]}", __package__)
    if args.command == "api-server":
        if remaining:
            parser.error("api-server accepts no command-line options; use HOST and PORT")
        module.main()
        return 0
    return module.main(remaining) or 0
