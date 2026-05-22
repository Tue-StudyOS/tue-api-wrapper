from __future__ import annotations

import json
from collections.abc import Iterable

from .praxisportal_dates import iso_from_timestamp
from .praxisportal_models import CareerSubscription, CareerSubscriptionQuery, CareerSubscriptionType


def build_praxisportal_subscription_query(
    *,
    text: Iterable[str] = (),
    project_type_ids: Iterable[int] = (),
    project_subtype_ids: Iterable[int] = (),
    industry_ids: Iterable[int] = (),
    postal_codes: Iterable[str] = (),
    in_english: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
) -> CareerSubscriptionQuery:
    return CareerSubscriptionQuery(
        in_english=in_english,
        start_date=start_date,
        end_date=end_date,
        text=_string_values(text),
        industries=_id_values(industry_ids),
        project_subtypes=_id_values(project_subtype_ids),
        postal_code=_string_values(postal_codes),
        project_type_id=_id_values(project_type_ids),
    )


def map_praxisportal_subscription_type(raw: dict[str, object]) -> CareerSubscriptionType:
    return CareerSubscriptionType(
        id=int(raw["id"]),
        title=str(raw.get("title", "")).strip(),
        short_name=str(raw.get("short_name", "")).strip(),
    )


def map_praxisportal_subscription(raw: dict[str, object]) -> CareerSubscription:
    keyword = raw.get("keyword", {})
    query = _subscription_query_from_raw(keyword.get("query") if isinstance(keyword, dict) else None)
    subscription_type = raw.get("subscription_type", {})
    return CareerSubscription(
        id=int(raw["id"]),
        user_id=int(raw.get("user_id", 0)),
        query_id=int(raw.get("query_id", 0)),
        subscription_type_id=int(raw.get("subscription_type_id", 0)),
        active=bool(int(raw.get("active", 0) or 0)),
        query=query,
        subscription_type=map_praxisportal_subscription_type(subscription_type if isinstance(subscription_type, dict) else {}),
        created_at=iso_from_timestamp(raw.get("created_at"), milliseconds=True),
        updated_at=iso_from_timestamp(raw.get("updated_at"), milliseconds=True),
    )


def _subscription_query_from_raw(raw_query: object) -> CareerSubscriptionQuery:
    if isinstance(raw_query, str) and raw_query.strip():
        payload = json.loads(raw_query)
    elif isinstance(raw_query, dict):
        payload = raw_query
    else:
        payload = {}
    return CareerSubscriptionQuery(
        in_english=bool(payload.get("in_english", False)),
        start_date=payload.get("start_date") if payload.get("start_date") else None,
        end_date=payload.get("end_date") if payload.get("end_date") else None,
        text=_string_values(payload.get("text", [])),
        industries=_string_values(payload.get("industries", [])),
        project_subtypes=_string_values(payload.get("project_subtypes", [])),
        postal_code=_string_values(payload.get("postal_code", [])),
        project_type_id=_string_values(payload.get("project_type_id", [])),
        version=str(payload.get("version", "2.0") or "2.0"),
    )


def _id_values(values: Iterable[int]) -> list[str]:
    return [str(value) for value in values]


def _string_values(values: object) -> list[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return []
    return [str(value).strip() for value in values if str(value).strip()]
