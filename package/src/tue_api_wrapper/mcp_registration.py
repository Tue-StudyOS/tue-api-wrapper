from __future__ import annotations

from pathlib import Path
from typing import Any

from .registration_workflows import inspect_registration, registration_options
from .study_radar_runtime import make_client


def register_registration_tools(server: Any, env_file: str | Path | None) -> None:
    def run(operation):
        client, _ = make_client(env_file)
        try:
            return operation(client.alma.client)
        finally:
            client.close()

    @server.tool()
    def alma_registration_inspect(kind: str, url: str, exam_id: str | None = None) -> dict[str, Any]:
        """Inspect an Alma course or exam registration. This does not submit a registration."""
        return run(lambda client: inspect_registration(client, kind, url, exam_id))

    @server.tool()
    def alma_registration_prepare(kind: str, url: str, exam_id: str | None = None) -> dict[str, Any]:
        """Read Alma registration options. If an instruction needs acceptance, stop and review it in Alma."""
        return run(lambda client: registration_options(client, kind, url, exam_id))
