"""Review and execute existing Alma registration flows."""
from __future__ import annotations

from typing import Any

from .alma_course_registration_client import inspect_course_registration_support, prepare_course_registration, register_for_course
from .alma_exam_registration_client import inspect_exam_registration_support, prepare_exam_registration, register_for_exam
from .portal_common import serialize


def inspect_registration(client: Any, kind: str, url: str, exam_id: str | None) -> dict[str, Any]:
    if kind == "course":
        return serialize(inspect_course_registration_support(client, url))
    if kind == "exam":
        return serialize(inspect_exam_registration_support(client, url, exam_unit_id=exam_id))
    raise ValueError("Unknown registration kind")


def _options(client: Any, kind: str, url: str, exam_id: str | None):
    if kind == "course":
        data = prepare_course_registration(client, url)
    elif kind == "exam":
        data = prepare_exam_registration(client, url, exam_unit_id=exam_id, allow_instruction_accept=False)
    else:
        raise ValueError("Unknown registration kind")
    return data


def registration_options(client: Any, kind: str, url: str, exam_id: str | None) -> dict[str, Any]:
    return serialize(_options(client, kind, url, exam_id))


def prepare_selected(client: Any, username: str, kind: str, url: str, exam_id: str | None, option_id: str) -> dict[str, Any]:
    data = _options(client, kind, url, exam_id)
    if data.action != "ANMELDUNG" or not data.title or not data.number:
        raise ValueError("Alma did not provide a clear registration action and target identity")
    resolved_exam_id = data.exam_unit_id if kind == "exam" else None
    if kind == "exam" and (not resolved_exam_id or (exam_id and exam_id != resolved_exam_id)):
        raise ValueError("Alma did not identify the requested exam unambiguously")
    options = [option for option in data.options if option.planelement_id == option_id]
    if len(options) != 1:
        raise ValueError("Select exactly one available registration option")
    return {"kind": kind, "target": url, "account": username, "title": data.title,
            "number": data.number, "action": data.action, "exam_unit_id": resolved_exam_id,
            "option": serialize(options[0]), "messages": list(data.messages)}


def execute_registration(client: Any, reviewed: dict[str, Any]) -> dict[str, Any]:
    option = reviewed["option"]
    common = {"planelement_id": option["planelement_id"], "expected_option_label": option["label"],
              "expected_title": reviewed["title"], "expected_number": reviewed["number"],
              "expected_action_name": option["action_name"]}
    try:
        if reviewed["kind"] == "course":
            result = register_for_course(client, reviewed["target"], **common)
        else:
            result = register_for_exam(client, reviewed["target"], exam_unit_id=reviewed["exam_unit_id"],
                                       allow_instruction_accept=False, **common)
    except Exception as error:
        return {"outcome": "unknown", "error": type(error).__name__,
                "message": "The action may have reached Alma. Check current registration before retrying."}
    try:
        checked = inspect_registration(client, reviewed["kind"], reviewed["target"], reviewed.get("exam_unit_id"))
    except Exception as error:
        return {"outcome": "unknown", "response": serialize(result), "verification_error": type(error).__name__}
    # Existing status parsers are heuristic and are not a receipt for a selected option.
    return {"outcome": "unverified", "response": serialize(result), "subsequent_inspection": checked,
            "message": "Confirm the selected registration in Alma; status parsing does not establish a receipt."}
