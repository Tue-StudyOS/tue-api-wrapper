"""Opt-in Moodle quiz attempt actions."""
from __future__ import annotations

from .moodle_quiz_start import review_start, start_attempt
from .moodle_quiz_answer import review_answers, save_answers
from .moodle_quiz_finish import review_finish, finish_attempt
from .study_radar_runtime import make_client
from .ilias_quiz_start import review_ilias_start, start_ilias_attempt
from .ilias_quiz_attempt import fetch_question as ilias_question
from .ilias_quiz_answers import review_answers as ilias_review_answers, save_answers as ilias_save_answers
from .ilias_quiz_finish import review_finish as ilias_review_finish, finish_attempt as ilias_finish


def register_quiz_write_tools(server, env_file):
    def run(operation):
        client, _ = make_client(env_file)
        try:
            return operation(client.moodle.client)
        finally:
            client.close()

    @server.tool()
    def moodle_quiz_review_start(quiz_id: int) -> dict:
        """Review the quiz and its available start action. Starting can consume an attempt and start a timer."""
        return run(lambda client: review_start(client, quiz_id))

    @server.tool()
    def moodle_quiz_start(quiz_id: int, review_sha256: str, confirm: bool = False) -> dict:
        """Start a reviewed quiz attempt; requires explicit confirmation and may start a timer."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run(lambda client: start_attempt(client, quiz_id, review_sha256, confirm=True))

    @server.tool()
    def moodle_quiz_review_answers(attempt_id: int, page: int, answers: dict[str, list[str]]) -> dict:
        """Review answer values for visible supported question fields without saving them."""
        return run(lambda client: review_answers(client, attempt_id, page, answers))

    @server.tool()
    def moodle_quiz_save_answers(attempt_id: int, page: int, answers: dict[str, list[str]],
                                 review_sha256: str, confirm: bool = False) -> dict:
        """Save reviewed answers on one attempt page; this does not intentionally finish the quiz."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run(lambda client: save_answers(client, attempt_id, page, answers, review_sha256, confirm=True))

    @server.tool()
    def moodle_quiz_review_finish(attempt_id: int) -> dict:
        """Review Moodle's attempt summary before submitting all answers for grading."""
        return run(lambda client: review_finish(client, attempt_id))

    @server.tool()
    def moodle_quiz_finish(attempt_id: int, review_sha256: str, confirm: bool = False) -> dict:
        """Finish the reviewed attempt; this submits answers and may be irreversible."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run(lambda client: finish_attempt(client, attempt_id, review_sha256, confirm=True))

    def run_ilias(operation):
        client, _ = make_client(env_file)
        try:
            return operation(client.ilias.client)
        finally:
            client.close()

    @server.tool()
    def ilias_quiz_review_start(quiz_id: int) -> dict:
        """Review the observed ILIAS start action; question support is limited and unverified live."""
        return run_ilias(lambda client: review_ilias_start(client, quiz_id))

    @server.tool()
    def ilias_quiz_start(quiz_id: int, review_sha256: str, confirm: bool = False) -> dict:
        """Request the reviewed ILIAS quiz start; the outcome requires inspection in ILIAS."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run_ilias(lambda client: start_ilias_attempt(client, quiz_id, review_sha256, confirm=True))

    @server.tool()
    def ilias_quiz_question(quiz_id: int) -> dict:
        """Resume an existing attempt and read its current supported question; this can restart its timer."""
        return run_ilias(lambda client: ilias_question(client, quiz_id))

    @server.tool()
    def ilias_quiz_review_answers(quiz_id: int, answers: dict[str, list[str]]) -> dict:
        """Resume an existing attempt and review answers; resuming can restart its timer."""
        return run_ilias(lambda client: ilias_review_answers(client, quiz_id, answers))

    @server.tool()
    def ilias_quiz_save_answers(quiz_id: int, answers: dict[str, list[str]],
                                review_sha256: str, confirm: bool = False) -> dict:
        """Save reviewed answers; depending on test settings this may lock them or trigger feedback."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run_ilias(lambda client: ilias_save_answers(client, quiz_id, answers, review_sha256, confirm=True))

    @server.tool()
    def ilias_quiz_review_finish(quiz_id: int) -> dict:
        """Resume an existing attempt and inspect ILIAS's finish confirmation; its timer may restart."""
        return run_ilias(lambda client: ilias_review_finish(client, quiz_id))

    @server.tool()
    def ilias_quiz_finish(quiz_id: int, review_sha256: str, confirm: bool = False) -> dict:
        """Finish the reviewed ILIAS attempt; this submits answers and can be irreversible."""
        if not confirm:
            raise ValueError('Explicit confirmation is required')
        return run_ilias(lambda client: ilias_finish(client, quiz_id, review_sha256, confirm=True))
