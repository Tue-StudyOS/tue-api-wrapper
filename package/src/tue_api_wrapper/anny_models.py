from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AnnyService:
    id: str
    name: str | None
    slug: str | None
    duration_label: str | None
    supports_instant_booking: bool | None
    min_duration: int | None = None
    max_duration: int | None = None
    booking_interval: int | None = None


@dataclass(slots=True)
class AnnyResourceProperty:
    id: str
    label: str
    value: object
    private: bool = False


@dataclass(slots=True)
class AnnyResource:
    id: str
    slug: str
    name: str
    source_url: str | None
    description: str | None = None
    category: str | None = None
    location: str | None = None
    image_url: str | None = None
    timezone: str | None = None
    quantity: int | None = None
    bookings_enabled: bool = False
    booking_requires_community: bool = False
    viewing_requires_community: bool = False
    services: list[AnnyService] = field(default_factory=list)
    properties: list[AnnyResourceProperty] = field(default_factory=list)


@dataclass(slots=True)
class AnnyResourcePage:
    source_url: str
    total_results: int
    total_pages: int
    current_page: int
    items: list[AnnyResource] = field(default_factory=list)


@dataclass(slots=True)
class AnnyTimeSlot:
    start_date: str
    end_date: str
    available: bool
    unit: str | None
    quota: int | None
    remaining_number_available: int | None
    unavailability_type: str | None
    messages: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AnnyAvailabilityDate:
    date: str
    available: bool
    timezone: str | None
    unavailability_type: str | None = None


@dataclass(slots=True)
class AnnyAvailabilityPeriod:
    id: str
    resource_id: str
    start_date: str
    end_date: str
    quota: int | None
    title: str | None = None


@dataclass(slots=True)
class AnnyCalendarEvent:
    id: str
    resource_id: str
    resource_name: str | None
    start_date: str
    end_date: str
    is_available: bool
    display_label: str | None
    occupancy: int | None
    quota: int | None
    available_intervals: list[AnnyTimeSlot] = field(default_factory=list)


@dataclass(slots=True)
class AnnyServiceConfiguration:
    resource_id: str
    service_id: str
    name: str | None
    next_available_date: str | None
    min_duration: int | None
    max_duration: int | None
    calculation_interval: int | None
    advance_booking_period: int | None
    duration_label: str | None
    price_label: str | None
    is_free: bool | None
    currency: str | None


@dataclass(slots=True)
class AnnyBookingQuote:
    resource_id: str
    service_id: str
    start_date: str | None
    end_date: str | None
    charged_duration: int | None
    total: int | float | None
    currency: str | None
    price_hidden: bool | None
    items: list[str] = field(default_factory=list)
