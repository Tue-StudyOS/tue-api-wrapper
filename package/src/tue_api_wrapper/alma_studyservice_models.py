from __future__ import annotations

from dataclasses import dataclass

from .alma_profile_models import AlmaProfileSection
from .models import AlmaDocumentReport


@dataclass(frozen=True)
class AlmaStudyServiceTab:
    button_name: str
    label: str
    is_active: bool


@dataclass(frozen=True)
class AlmaStudyServiceOutputRequest:
    trigger_name: str
    label: str
    count: int | None
    message: str | None


@dataclass(frozen=True)
class AlmaStudyServicePage:
    action_url: str
    payload: dict[str, str]
    reports: tuple[AlmaDocumentReport, ...]
    latest_download_url: str | None
    banner_text: str | None
    person_name: str | None
    active_tab_label: str | None
    tabs: tuple[AlmaStudyServiceTab, ...]
    output_requests: tuple[AlmaStudyServiceOutputRequest, ...]
    contact_sections: tuple[AlmaProfileSection, ...]
