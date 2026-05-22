from __future__ import annotations

import json
from functools import lru_cache
from urllib.parse import quote

import requests

from .config import DEFAULT_TIMEOUT_SECONDS
from .praxisportal_auth import PraxisportalAuthMixin
from .praxisportal_dates import iso_from_timestamp
from .praxisportal_filters import (
    build_praxisportal_filter_expression,
    build_praxisportal_filter_options,
    build_praxisportal_postal_code_options,
    build_visibility_filter,
)
from .praxisportal_models import (
    CareerOrganization,
    CareerProjectDetail,
    CareerProjectSummary,
    CareerSearchFilters,
    CareerSearchResponse,
)
from .praxisportal_subscription_client import PraxisportalSubscriptionMixin
from .praxisportal_subscriptions import (
    build_praxisportal_subscription_query,
    map_praxisportal_subscription,
)

PRAXISPORTAL_BASE_URL = "https://www.praxisportal.uni-tuebingen.de"
ALGOLIA_APP_ID = "ESD35NPPR9"
ALGOLIA_API_KEY = "fc3088fb6da3aa814eb902f0635f46b3"
ALGOLIA_INDEX = "projects_prd"
ALGOLIA_NEWEST_INDEX = f"{ALGOLIA_INDEX}_newest"


def _algolia_headers() -> dict[str, str]:
    return {
        "content-type": "application/json",
        "x-algolia-application-id": ALGOLIA_APP_ID,
        "x-algolia-api-key": ALGOLIA_API_KEY,
    }


def _algolia_post(path: str, payload: dict[str, object], *, timeout: int) -> dict[str, object]:
    response = requests.post(
        f"https://{ALGOLIA_APP_ID}-dsn.algolia.net{path}",
        headers=_algolia_headers(),
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _algolia_get(path: str, *, timeout: int) -> dict[str, object]:
    response = requests.get(
        f"https://{ALGOLIA_APP_ID}-dsn.algolia.net{path}",
        headers=_algolia_headers(),
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _preview_from_text(value: str | None, *, limit: int = 220) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def map_praxisportal_summary(hit: dict[str, object]) -> CareerProjectSummary:
    project_types = [str(item.get("name", "")).strip() for item in hit.get("project_type", []) if str(item.get("name", "")).strip()]
    industries = [str(item.get("title", "")).strip() for item in hit.get("industry", []) if str(item.get("title", "")).strip()]
    organizations = [str(item.get("name", "")).strip() for item in hit.get("organization", []) if str(item.get("name", "")).strip()]
    project_id = int(hit["id"])
    return CareerProjectSummary(
        id=project_id,
        title=str(hit.get("title", "")).strip(),
        preview=_preview_from_text(str(hit.get("job_description", "") or "")),
        location=(str(hit.get("location", "")).strip() or None),
        project_types=project_types,
        industries=industries,
        organizations=organizations,
        created_at=iso_from_timestamp(hit.get("created_at"), milliseconds=True),
        start_date=iso_from_timestamp(hit.get("start_date")),
        end_date=iso_from_timestamp(hit.get("end_date")),
        source_url=f"{PRAXISPORTAL_BASE_URL}/projects/{project_id}",
    )


def map_praxisportal_detail(hit: dict[str, object]) -> CareerProjectDetail:
    project_id = int(hit["id"])
    return CareerProjectDetail(
        id=project_id,
        title=str(hit.get("title", "")).strip(),
        location=(str(hit.get("location", "")).strip() or None),
        description=(str(hit.get("job_description", "")).strip() or None),
        requirements=(str(hit.get("requirements", "")).strip() or None),
        project_types=[str(item.get("name", "")).strip() for item in hit.get("project_type", []) if str(item.get("name", "")).strip()],
        industries=[str(item.get("title", "")).strip() for item in hit.get("industry", []) if str(item.get("title", "")).strip()],
        organizations=[
            CareerOrganization(
                id=(int(item["id"]) if item.get("id") is not None else None),
                name=str(item.get("name", "")).strip(),
                logo_url=(str(item.get("logo", "")).strip() or None),
            )
            for item in hit.get("organization", [])
            if str(item.get("name", "")).strip()
        ],
        created_at=iso_from_timestamp(hit.get("created_at"), milliseconds=True),
        start_date=iso_from_timestamp(hit.get("start_date")),
        end_date=iso_from_timestamp(hit.get("end_date")),
        source_url=f"{PRAXISPORTAL_BASE_URL}/projects/{project_id}",
    )


class PraxisportalClient(PraxisportalAuthMixin, PraxisportalSubscriptionMixin):
    def __init__(self, *, timeout: int = DEFAULT_TIMEOUT_SECONDS, session: requests.Session | None = None) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "tue-api-wrapper/0.1 (+https://www.praxisportal.uni-tuebingen.de/)")

    def search_projects(
        self,
        *,
        query: str = "",
        project_type_ids: tuple[int, ...] = (),
        project_subtype_ids: tuple[int, ...] = (),
        industry_ids: tuple[int, ...] = (),
        postal_codes: tuple[str, ...] = (),
        organization_ids: tuple[int, ...] = (),
        page: int = 0,
        per_page: int = 20,
        sort: str = "newest",
    ) -> CareerSearchResponse:
        params = {
            "query": query or None,
            "optionalWords": query or None,
            "filters": build_praxisportal_filter_expression(
                project_type_ids=project_type_ids,
                project_subtype_ids=project_subtype_ids,
                industry_ids=industry_ids,
                postal_codes=postal_codes,
                organization_ids=organization_ids,
            ),
            "hitsPerPage": per_page,
            "page": page,
            "facets": [],
        }
        params_str = "&".join(f"{key}={quote(str(value), safe='[]:,()<> ')}" for key, value in params.items() if value is not None)
        index = ALGOLIA_NEWEST_INDEX if sort == "newest" else ALGOLIA_INDEX
        payload = _algolia_post(f"/1/indexes/{index}/query", {"params": params_str}, timeout=self.timeout)
        filters = self.fetch_filter_options()
        return CareerSearchResponse(
            query=query,
            page=int(payload.get("page", 0)),
            per_page=int(payload.get("hitsPerPage", per_page)),
            total_hits=int(payload.get("nbHits", 0)),
            total_pages=int(payload.get("nbPages", 0)),
            source_url=f"{PRAXISPORTAL_BASE_URL}/candidate/search",
            filters=filters,
            items=[map_praxisportal_summary(hit) for hit in payload.get("hits", [])],
        )

    def fetch_project(self, project_id: int) -> CareerProjectDetail:
        object_id = quote(f"App\\Models\\Project::{project_id}", safe="")
        payload = _algolia_get(f"/1/indexes/{ALGOLIA_INDEX}/{object_id}", timeout=self.timeout)
        return map_praxisportal_detail(payload)

    @lru_cache(maxsize=1)
    def fetch_filter_options(self) -> CareerSearchFilters:
        facets = ["project_type.id", "subproject_type.id", "industry.id", "organization.id", "postal_code"]
        payload = _algolia_post(
            f"/1/indexes/{ALGOLIA_INDEX}/query",
            {
                "params": (
                    f"query=&hitsPerPage=0&facets={quote(json.dumps(facets), safe='[]\",.')}"
                    f"&responseFields={quote('[\"facets\"]', safe='[]\"')}"
                    f"&filters={quote(build_visibility_filter(), safe='()<>:= ')}"
                )
            },
            timeout=self.timeout,
        )
        raw_facets = payload.get("facets", {})
        project_type_counts = raw_facets.get("project_type.id", {})
        project_subtype_counts = raw_facets.get("subproject_type.id", {})
        industry_counts = raw_facets.get("industry.id", {})
        organization_counts = raw_facets.get("organization.id", {})
        postal_code_counts = raw_facets.get("postal_code", {})
        project_type_labels = self._facet_labels("project_type.id", [int(value) for value in project_type_counts])
        project_subtype_labels = self._facet_labels("subproject_type.id", [int(value) for value in project_subtype_counts])
        industry_labels = self._facet_labels("industry.id", [int(value) for value in industry_counts])
        organization_ids = [int(value) for value in list(organization_counts)[:40]]
        postal_codes = list(postal_code_counts)[:50]
        postal_labels, postal_locations = self._postal_code_labels(postal_codes)
        return CareerSearchFilters(
            project_types=build_praxisportal_filter_options(project_type_counts, project_type_labels),
            project_subtypes=build_praxisportal_filter_options(project_subtype_counts, project_subtype_labels),
            industries=build_praxisportal_filter_options(industry_counts, industry_labels),
            organizations=build_praxisportal_filter_options(organization_counts, self._facet_labels("organization.id", organization_ids)),
            postal_codes=build_praxisportal_postal_code_options(postal_code_counts, postal_labels, postal_locations),
        )

    def _facet_labels(self, facet_name: str, ids: list[int]) -> dict[int, str]:
        requests_payload = [
            {
                "indexName": ALGOLIA_INDEX,
                "params": (
                    f"query=&hitsPerPage=1&filters={quote(build_visibility_filter() + ' AND ' + facet_name + ':' + str(value), safe='()<>:= ')}"
                ),
            }
            for value in ids
        ]
        payload = _algolia_post("/1/indexes/*/queries", {"requests": requests_payload}, timeout=self.timeout)
        labels: dict[int, str] = {}
        for value, result in zip(ids, payload.get("results", []), strict=False):
            hits = result.get("hits", [])
            if not hits:
                continue
            hit = hits[0]
            if facet_name == "project_type.id":
                match = next((item for item in hit.get("project_type", []) if int(item.get("id", -1)) == value), None)
                if match is not None:
                    labels[value] = str(match.get("name", "")).strip()
            if facet_name == "industry.id":
                match = next((item for item in hit.get("industry", []) if int(item.get("id", -1)) == value), None)
                if match is not None:
                    labels[value] = str(match.get("title", "")).strip()
            if facet_name == "subproject_type.id":
                match = next((item for item in hit.get("subproject_type", []) if int(item.get("id", -1)) == value), None)
                if match is not None:
                    labels[value] = str(match.get("name", "")).strip()
            if facet_name == "organization.id":
                match = next((item for item in hit.get("organization", []) if int(item.get("id", -1)) == value), None)
                if match is not None:
                    labels[value] = str(match.get("name", "")).strip()
        return labels

    def _postal_code_labels(self, postal_codes: list[str]) -> tuple[dict[str, str], dict[str, str]]:
        requests_payload = [
            {
                "indexName": ALGOLIA_INDEX,
                "params": f"query=&hitsPerPage=1&filters={quote(build_visibility_filter() + ' AND postal_code:' + code, safe='()<>:= ')}",
            }
            for code in postal_codes
        ]
        payload = _algolia_post("/1/indexes/*/queries", {"requests": requests_payload}, timeout=self.timeout)
        labels: dict[str, str] = {}
        locations: dict[str, str] = {}
        for code, result in zip(postal_codes, payload.get("results", []), strict=False):
            hits = result.get("hits", [])
            if not hits:
                continue
            location = str(hits[0].get("location", "")).strip()
            if location and location != code:
                labels[code] = f"{code} {location}"
                locations[code] = location
        return labels, locations
