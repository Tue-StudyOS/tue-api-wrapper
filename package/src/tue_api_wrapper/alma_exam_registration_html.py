from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from .alma_exam_registration_helpers import (
    clean_text,
    control_identity,
    extract_jsf_fields,
    find_detail_form,
    find_enroll_form,
    first_target,
    option_label,
)
from .alma_exam_registration_models import AlmaExamRegistrationOption
from .config import AlmaParseError
from .html_forms import extract_form_payload

EXAM_REGISTRATION_ACTION = "ANMELDUNG"


@dataclass(frozen=True)
class AlmaExamDetailOpenRequest:
    action_url: str
    payload: dict[str, str]
    enctype: str | None
    exam_unit_id: str


@dataclass(frozen=True)
class AlmaExamRegistrationStartRequest:
    action_url: str
    payload: dict[str, str]
    enctype: str | None
    title: str | None
    number: str | None
    exam_unit_id: str | None
    action: str


@dataclass(frozen=True)
class AlmaExamInstructionAcceptRequest:
    action_url: str
    payload: dict[str, str]


@dataclass(frozen=True)
class AlmaExamRegistrationConfirmRequest:
    action_url: str
    payload: dict[str, str]
    selected_option: AlmaExamRegistrationOption


def build_exam_detail_open_request(
    html: str,
    page_url: str,
    *,
    exam_unit_id: str | None = None,
) -> AlmaExamDetailOpenRequest:
    soup = BeautifulSoup(html, "html.parser")
    form = find_detail_form(soup)
    if not isinstance(form, Tag):
        raise AlmaParseError("Alma did not expose the timetable detail form.")

    candidates = _exam_detail_candidates(form)
    requested = (exam_unit_id or "").strip()
    if requested:
        candidates = [candidate for candidate in candidates if candidate[1] == requested]
    if not candidates:
        raise AlmaParseError("Alma did not expose a linked exam detail action.")
    if len(candidates) > 1:
        raise AlmaParseError("Multiple Alma exam detail actions are available; pass exam_unit_id.")

    target, selected_exam_unit_id = candidates[0]
    form_id = form.get("id") or form.get("name") or "detailViewData"
    payload = extract_form_payload(form)
    payload.setdefault(f"{form_id}_SUBMIT", "1")
    payload["linkedExamUnitId"] = selected_exam_unit_id
    payload[f"{form_id}:_idcl"] = target
    return AlmaExamDetailOpenRequest(
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
        enctype=form.get("enctype"),
        exam_unit_id=selected_exam_unit_id,
    )


def extract_exam_registration_start_request(html: str, page_url: str) -> AlmaExamRegistrationStartRequest | None:
    soup = BeautifulSoup(html, "html.parser")
    form = find_detail_form(soup)
    if not isinstance(form, Tag):
        return None

    target, js_fields = _find_exam_registration_target(form)
    if target is None:
        return None

    form_id = form.get("id") or form.get("name") or "detailViewData"
    payload = extract_form_payload(form)
    payload.update({key: value for key, value in js_fields.items() if key in {"unitId", "periodUsageId", "planelementId"}})
    payload.setdefault(f"{form_id}_SUBMIT", "1")
    payload[f"{form_id}:_idcl"] = target
    payload["belegungsAktion"] = payload.get("belegungsAktion") or EXAM_REGISTRATION_ACTION
    _fill_detail_identifiers(payload, page_url)

    title, number = _extract_exam_identity(html)
    return AlmaExamRegistrationStartRequest(
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
        enctype=form.get("enctype"),
        title=title,
        number=number,
        exam_unit_id=payload.get("unitId") or None,
        action=payload["belegungsAktion"],
    )


def build_instruction_accept_request(html: str, page_url: str) -> AlmaExamInstructionAcceptRequest | None:
    soup = BeautifulSoup(html, "html.parser")
    form = find_enroll_form(soup)
    if not isinstance(form, Tag):
        return None

    accept = form.find(attrs={"name": lambda value: bool(value and value.endswith(":enrollAccept"))})
    confirm = form.find(attrs={"name": lambda value: bool(value and value.endswith(":confirmInstruction"))})
    if accept is None or confirm is None:
        return None

    accept_name = accept.get("name")
    confirm_name = confirm.get("name")
    payload = extract_form_payload(form)
    payload[confirm_name] = "true"
    payload[accept_name] = accept.get("value") or accept.get_text(" ", strip=True) or "Weiter"
    payload["activePageElementId"] = accept_name
    payload["refreshButtonClickedId"] = ""
    return AlmaExamInstructionAcceptRequest(
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
    )


def build_exam_registration_confirm_request(
    html: str,
    page_url: str,
    *,
    planelement_id: str | None = None,
) -> AlmaExamRegistrationConfirmRequest:
    options = extract_exam_registration_options(html)
    selected = _select_option(options, planelement_id)
    soup = BeautifulSoup(html, "html.parser")
    form = find_enroll_form(soup)
    if not isinstance(form, Tag):
        raise AlmaParseError("Alma did not expose the exam-registration confirmation form.")

    form_id = form.get("id") or form.get("name") or "enrollForm"
    payload = extract_form_payload(form)
    payload.setdefault(f"{form_id}_SUBMIT", "1")
    payload["planelementId"] = selected.planelement_id
    payload["belegungsAktion"] = EXAM_REGISTRATION_ACTION
    payload[f"{form_id}:_idcl"] = selected.action_name
    return AlmaExamRegistrationConfirmRequest(
        action_url=urljoin(page_url, form.get("action", page_url)),
        payload=payload,
        selected_option=selected,
    )


def extract_exam_registration_options(html: str) -> tuple[AlmaExamRegistrationOption, ...]:
    soup = BeautifulSoup(html, "html.parser")
    form = find_enroll_form(soup)
    if not isinstance(form, Tag):
        return ()

    options: list[AlmaExamRegistrationOption] = []
    seen: set[tuple[str, str]] = set()
    for control in form.find_all(["button", "input", "a"]):
        action_name = _confirm_action_name(control)
        if action_name is None:
            continue
        planelement_id = _extract_planelement_id(control)
        if not planelement_id:
            continue
        key = (planelement_id, action_name)
        if key in seen:
            continue
        seen.add(key)
        options.append(
            AlmaExamRegistrationOption(
                planelement_id=planelement_id,
                label=option_label(control, len(options)),
                action_name=action_name,
            )
        )
    return tuple(options)


def extract_exam_registration_messages(html: str) -> tuple[str, ...]:
    soup = BeautifulSoup(html, "html.parser")
    messages: list[str] = []
    seen: set[str] = set()
    for selector in (
        "ul.listMessages li",
        ".messages-infobox-scroll-container li",
        ".ui-messages li",
        "[class*=messages] li",
        "[id*=messages] li",
        ".messages-infobox-scroll-container",
        "[class*=messages-infobox]",
    ):
        for node in soup.select(selector):
            message = clean_text(node.get_text(" ", strip=True))
            if message and message not in seen:
                seen.add(message)
                messages.append(message)
    return tuple(messages)


def extract_exam_registration_status(html: str, messages: tuple[str, ...]) -> str | None:
    text = clean_text(" ".join((*messages, BeautifulSoup(html, "html.parser").get_text(" ", strip=True))))
    if re.search(r"\b(bestätigung|aenderung|änderung)\b", text, re.IGNORECASE):
        return "registered"
    text_without_negative = re.sub(r"\bnicht\s+angemeldet\b", "", text, flags=re.IGNORECASE)
    if re.search(r"\bangemeldet\b", text_without_negative, re.IGNORECASE):
        return "registered"
    if re.search(r"\b(nicht\s+angemeldet|abgemeldet)\b", text, re.IGNORECASE):
        return "not_registered"
    return None


def _exam_detail_candidates(form: Tag) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for control in form.find_all(["button", "input", "a"]):
        fields = extract_jsf_fields(control.get("onclick", ""))
        target = control.get("name") or control.get("id") or first_target(fields, "showDetailsViewForLinkedExamination")
        exam_unit_id = fields.get("linkedExamUnitId")
        identity = control_identity(control)
        if target and exam_unit_id and "showdetailsviewforlinkedexamination" in identity:
            candidates.append((target, exam_unit_id))
    return candidates


def _find_exam_registration_target(form: Tag) -> tuple[str | None, dict[str, str]]:
    for control in form.find_all(["button", "input", "a"]):
        identity = control_identity(control)
        if "anmeld" not in identity or "examinationperiod" not in identity:
            continue
        fields = extract_jsf_fields(control.get("onclick", ""))
        return control.get("name") or control.get("id") or first_target(fields, "anmelden"), fields
    return None, {}


def _confirm_action_name(control: Tag) -> str | None:
    name = control.get("name") or control.get("id")
    if name and "anechtzeit" in name.casefold():
        return name
    return first_target(extract_jsf_fields(control.get("onclick", "")), "anEchtzeit")


def _extract_planelement_id(control: Tag) -> str | None:
    fields = extract_jsf_fields(control.get("onclick", ""))
    if fields.get("planelementId"):
        return fields["planelementId"]
    row = control.find_parent("tr")
    hidden = row.find(attrs={"name": "planelementId"}) if row is not None else None
    return hidden.get("value") if hidden is not None and hidden.get("value") else None


def _select_option(options: tuple[AlmaExamRegistrationOption, ...], planelement_id: str | None) -> AlmaExamRegistrationOption:
    requested = (planelement_id or "").strip()
    if requested:
        for option in options:
            if option.planelement_id == requested:
                return option
        raise AlmaParseError(f"Unknown Alma exam-registration path '{requested}'.")
    if not options:
        raise AlmaParseError("Alma did not expose a selectable exam-registration path.")
    if len(options) > 1:
        raise AlmaParseError("Multiple Alma exam-registration paths are available; pass planelement_id.")
    return options[0]


def _fill_detail_identifiers(payload: dict[str, str], page_url: str) -> None:
    query = parse_qs(urlparse(page_url).query)
    for name in ("unitId", "periodUsageId", "planelementId"):
        payload.setdefault(name, query.get(name, [""])[0])
    payload.setdefault("wunschVerbuchungspfad", "")


def _extract_exam_identity(html: str) -> tuple[str | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup.get_text(" ", strip=True))
    match = re.search(r"([A-ZÄÖÜ]+[A-ZÄÖÜ0-9-]*):\s+([^:]+?)\s+Leistung wird verwendet", text)
    if match:
        return match.group(2).strip(), match.group(1).strip()
    return None, None

