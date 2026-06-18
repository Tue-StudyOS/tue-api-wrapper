from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlmaEnrollmentEntry:
    title: str
    number: str | None
    event_type: str | None
    status: str | None
    semester: str | None
    schedule_text: str | None
    detail_url: str | None
    attempt: str | None = None
    category: str | None = None
