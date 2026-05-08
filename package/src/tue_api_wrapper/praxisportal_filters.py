from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from .config import GERMAN_TIMEZONE
from .praxisportal_models import CareerFacetOption, CareerPostalCodeOption


def build_visibility_filter() -> str:
    now = datetime.now(GERMAN_TIMEZONE)
    day_start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()) - 100
    day_end = int((now.replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(seconds=100)).timestamp())
    return (
        f"(blocked<1 AND hidden<1 AND project_stop_date>={day_start} "
        f"AND project_start_date<={day_end}) AND (visible_institutes:-1)"
    )


def build_praxisportal_filter_expression(
    *,
    project_type_ids: Iterable[int] = (),
    project_subtype_ids: Iterable[int] = (),
    industry_ids: Iterable[int] = (),
    postal_codes: Iterable[str] = (),
    organization_ids: Iterable[int] = (),
) -> str:
    clauses = [build_visibility_filter()]
    project_filters = [f"project_type.id:{value}" for value in project_type_ids]
    project_filters.extend(f"subproject_type.id:{value}" for value in project_subtype_ids)
    industry_filters = [f"industry.id:{value}" for value in industry_ids]
    postal_code_filters = [f"postal_code:{value}" for value in _clean_postal_codes(postal_codes)]
    organization_filters = [f"organization.id:{value}" for value in organization_ids]
    for group in (project_filters, industry_filters, postal_code_filters, organization_filters):
        if group:
            clauses.append("(" + " OR ".join(group) + ")")
    return " AND ".join(clauses)


def build_praxisportal_filter_options(counts: dict[str, int], labels: dict[int, str]) -> list[CareerFacetOption]:
    options = [
        CareerFacetOption(id=int(key), label=labels[int(key)], count=int(value))
        for key, value in counts.items()
        if int(key) in labels
    ]
    return sorted(options, key=lambda option: option.label.lower())


def build_praxisportal_postal_code_options(
    counts: dict[str, int],
    labels: dict[str, str],
    locations: dict[str, str],
) -> list[CareerPostalCodeOption]:
    options = [
        CareerPostalCodeOption(
            code=code,
            label=labels.get(code, code),
            count=int(count),
            location=locations.get(code),
        )
        for code, count in counts.items()
        if code.strip()
    ]
    return sorted(options, key=lambda option: (-option.count, option.label.lower()))


def _clean_postal_codes(values: Iterable[str]) -> list[str]:
    return [str(value).strip() for value in values if str(value).strip()]
