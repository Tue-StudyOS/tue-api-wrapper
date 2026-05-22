from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlmaProfileField:
    label: str
    value: str


@dataclass(frozen=True)
class AlmaProfileSection:
    title: str
    fields: tuple[AlmaProfileField, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AlmaStudentProfile:
    person_name: str | None
    email_addresses: tuple[str, ...]
    postal_addresses: tuple[str, ...]
    sections: tuple[AlmaProfileSection, ...]
    source_tab_label: str | None
    source_page_url: str
