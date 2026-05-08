from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CareerFacetOption:
    id: int
    label: str
    count: int


@dataclass(slots=True)
class CareerPostalCodeOption:
    code: str
    label: str
    count: int
    location: str | None = None


@dataclass(slots=True)
class CareerSearchFilters:
    project_types: list[CareerFacetOption] = field(default_factory=list)
    project_subtypes: list[CareerFacetOption] = field(default_factory=list)
    industries: list[CareerFacetOption] = field(default_factory=list)
    organizations: list[CareerFacetOption] = field(default_factory=list)
    postal_codes: list[CareerPostalCodeOption] = field(default_factory=list)
    subscription_types: list["CareerSubscriptionType"] = field(default_factory=list)


@dataclass(slots=True)
class CareerOrganization:
    id: int | None
    name: str
    logo_url: str | None


@dataclass(slots=True)
class CareerProjectSummary:
    id: int
    title: str
    preview: str | None
    location: str | None
    project_types: list[str]
    industries: list[str]
    organizations: list[str]
    created_at: str | None
    start_date: str | None
    end_date: str | None
    source_url: str


@dataclass(slots=True)
class CareerProjectDetail:
    id: int
    title: str
    location: str | None
    description: str | None
    requirements: str | None
    project_types: list[str]
    industries: list[str]
    organizations: list[CareerOrganization] = field(default_factory=list)
    created_at: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    source_url: str | None = None


@dataclass(slots=True)
class CareerSearchResponse:
    query: str
    page: int
    per_page: int
    total_hits: int
    total_pages: int
    source_url: str
    filters: CareerSearchFilters
    items: list[CareerProjectSummary] = field(default_factory=list)


@dataclass(slots=True)
class CareerSubscriptionType:
    id: int
    title: str
    short_name: str


@dataclass(slots=True)
class CareerSubscriptionQuery:
    in_english: bool = False
    start_date: str | None = None
    end_date: str | None = None
    text: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    project_subtypes: list[str] = field(default_factory=list)
    postal_code: list[str] = field(default_factory=list)
    project_type_id: list[str] = field(default_factory=list)
    version: str = "2.0"

    def create_payload(self) -> dict[str, object]:
        return {
            "in_english": self.in_english,
            "start_date": self.start_date or "",
            "end_date": self.end_date or "",
            "text": self.text,
            "industries": self.industries,
            "project_subtypes": self.project_subtypes,
            "postal_code": self.postal_code,
            "project_type_id": self.project_type_id,
            "version": self.version,
        }


@dataclass(slots=True)
class CareerSubscription:
    id: int
    user_id: int
    query_id: int
    subscription_type_id: int
    active: bool
    query: CareerSubscriptionQuery
    subscription_type: CareerSubscriptionType
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True)
class CareerUser:
    id: int
    username: str
    fullname: str
    institute_id: int | None = None
