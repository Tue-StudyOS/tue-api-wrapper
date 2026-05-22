from __future__ import annotations

import re

from .alma_profile_models import AlmaStudentProfile
from .alma_studyservice_client import fetch_studyservice_contract

CONTACT_TAB_LABEL = "Kontaktdaten"
_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_ADDRESS_LABELS = ("adresse", "anschrift", "address")


def fetch_student_profile(client) -> AlmaStudentProfile:
    page = fetch_studyservice_contract(client, tab_label=CONTACT_TAB_LABEL)
    email_addresses = _unique(
        email
        for section in page.contact_sections
        for field in section.fields
        for email in _EMAIL_RE.findall(field.value)
    )
    postal_addresses = _unique(
        field.value
        for section in page.contact_sections
        for field in section.fields
        if _is_address_label(field.label)
    )
    return AlmaStudentProfile(
        person_name=page.person_name,
        email_addresses=email_addresses,
        postal_addresses=postal_addresses,
        sections=page.contact_sections,
        source_tab_label=page.active_tab_label,
        source_page_url=client.studyservice_url,
    )


def _is_address_label(label: str) -> bool:
    normalized = label.casefold()
    return any(needle in normalized for needle in _ADDRESS_LABELS)


def _unique(values) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = "\n".join(line.strip() for line in str(value).splitlines() if line.strip())
        key = cleaned.casefold()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return tuple(unique)
