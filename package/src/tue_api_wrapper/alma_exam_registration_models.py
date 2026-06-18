from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlmaExamRegistrationOption:
    planelement_id: str
    label: str
    action_name: str


@dataclass(frozen=True)
class AlmaExamRegistrationSupport:
    source_url: str
    title: str | None
    number: str | None
    exam_unit_id: str | None
    supported: bool
    action: str | None
    status: str | None = None
    messages: tuple[str, ...] = ()
    message: str | None = None


@dataclass(frozen=True)
class AlmaExamRegistrationOptions:
    source_url: str
    title: str | None
    number: str | None
    exam_unit_id: str | None
    action: str
    options: tuple[AlmaExamRegistrationOption, ...]
    messages: tuple[str, ...]
    requires_instruction_accept: bool


@dataclass(frozen=True)
class AlmaExamRegistrationResult:
    source_url: str
    final_url: str
    title: str | None
    number: str | None
    exam_unit_id: str | None
    action: str
    selected_option: AlmaExamRegistrationOption
    messages: tuple[str, ...]
    status: str | None
