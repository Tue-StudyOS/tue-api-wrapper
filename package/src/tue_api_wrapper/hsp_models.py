from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HspLocation:
    id: int
    name: str
    latitude: float | None
    longitude: float | None


@dataclass(slots=True)
class HspPrice:
    amount: str
    audience: str


@dataclass(slots=True)
class HspScheduleSlot:
    day: str | None
    time: str | None
    location: HspLocation | None


@dataclass(slots=True)
class HspCourse:
    id: str
    title: str
    subtitle: str | None
    area: str | None
    date_range: str | None
    instructor: str | None
    price_summary: str | None
    prices: list[HspPrice] = field(default_factory=list)
    schedules: list[HspScheduleSlot] = field(default_factory=list)
    is_bookable: bool = False
    booking_starts_at: str | None = None
    detail_url: str | None = None


@dataclass(slots=True)
class HspCourseSearchResult:
    source_url: str
    total_hits: int
    items: list[HspCourse] = field(default_factory=list)


@dataclass(slots=True)
class HspBookingOption:
    course_id: str
    title: str
    subtitle: str | None
    location: str | None
    date_range: str | None
    instructor: str | None
    price_summary: str | None
    prices: list[HspPrice] = field(default_factory=list)
    booking_label: str | None = None
    booking_submit_name: str | None = None
    booking_submit_value: str | None = None
    location_url: str | None = None
    info_url: str | None = None


@dataclass(slots=True)
class HspOfferPage:
    title: str
    responsible: str | None
    source_url: str
    booking_form_action: str | None
    booking_code: str | None
    items: list[HspBookingOption] = field(default_factory=list)
