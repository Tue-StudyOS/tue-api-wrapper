"""Opt-in MCP tools for reviewed Moodle file submission actions."""
from __future__ import annotations

from .moodle_submission_final import review_final, submit_final
from .moodle_submission_write import file_details, review_file, save_file, verify_file_receipt
from .study_radar_runtime import make_client


def register_moodle_write_tools(server, env_file):
    def run(operation):
        client, _ = make_client(env_file)
        try:
            return operation(client.moodle.client)
        finally:
            client.close()

    @server.tool()
    def moodle_submission_review(assignment_id: int, file_path: str, replace_existing: bool = False) -> dict:
        """Review local file and assignment before upload; opening the form may initialize a draft area."""
        return run(lambda client: review_file(client, assignment_id, file_path, replace_existing=replace_existing))

    @server.tool()
    def moodle_submission_save(assignment_id: int, file_path: str, sha256: str, review_sha256: str,
                               confirm: bool = False, replace_existing: bool = False) -> dict:
        """Upload and save the reviewed file. Saving may submit for grading or affect a group."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run(lambda client: save_file(client, assignment_id, file_path, sha256, review_sha256,
                                            confirm=confirm, replace_existing=replace_existing))

    @server.tool()
    def moodle_submission_review_final(assignment_id: int, file_path: str) -> dict:
        """Verify the saved draft and show the exact final confirmation text."""
        return run(lambda client: review_final(client, assignment_id, file_path))

    @server.tool()
    def moodle_submission_submit(assignment_id: int, file_path: str, sha256: str, confirmation_sha256: str,
                                 confirm: bool = False, accept_statement: bool = False) -> dict:
        """Submit the reviewed draft for grading. Confirm the declaration separately if required."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run(lambda client: submit_final(client, assignment_id, file_path, sha256, confirmation_sha256,
                                               confirm=confirm, accept_statement=accept_statement))

    @server.tool()
    def moodle_submission_verify(assignment_id: int, file_path: str) -> dict:
        """Re-read Moodle status and compare the saved file's bytes with the local file."""
        return run(lambda client: verify_file_receipt(client, assignment_id, file_details(file_path)))
