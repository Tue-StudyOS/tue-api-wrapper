"""Opt-in tools for posting reviewed Moodle forum messages."""
from __future__ import annotations

from .moodle_forum_write import publish_post, review_post
from .ilias_forum_write import publish_ilias_post, review_ilias_post
from .study_radar_runtime import make_client


def register_forum_write_tools(server, env_file):
    def run(operation):
        client, _ = make_client(env_file)
        try:
            return operation(client.moodle.client)
        finally:
            client.close()

    @server.tool()
    def moodle_forum_review(mode: str, target: int, subject: str, message: str) -> dict:
        """Review a new discussion or reply; target is the forum activity ID or parent post ID."""
        return run(lambda client: review_post(client, mode, target, subject, message))

    @server.tool()
    def moodle_forum_publish(mode: str, target: int, subject: str, message: str,
                             review_sha256: str, confirm: bool = False) -> dict:
        """Publish the reviewed message to other forum participants; requires explicit confirmation."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run(lambda client: publish_post(client, mode, target, subject, message, review_sha256, confirm=True))

    def run_ilias(operation):
        client, _ = make_client(env_file)
        try:
            return operation(client.ilias.client)
        finally:
            client.close()

    @server.tool()
    def ilias_forum_review(mode: str, target: str, subject: str, message: str, parent_id: str | None = None) -> dict:
        """Review an ILIAS discussion or reply; opening the editor can initialize a draft."""
        return run_ilias(lambda client: review_ilias_post(client, mode, target, subject, message, parent_id))

    @server.tool()
    def ilias_forum_publish(mode: str, target: str, subject: str, message: str, review_sha256: str,
                            confirm: bool = False, parent_id: str | None = None) -> dict:
        """Publish a reviewed ILIAS message. Inspect ILIAS before retrying if the receipt is unknown."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run_ilias(lambda client: publish_ilias_post(client, mode, target, subject, message,
                                                            review_sha256, confirm=True, parent_id=parent_id))
