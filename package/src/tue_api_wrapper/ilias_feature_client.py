from __future__ import annotations

import re

from .config import AlmaParseError
from .ilias_client import IliasClient
from .ilias_feature_html import ILIAS_SEARCH_URL, extract_ilias_search_form, parse_ilias_info_page, parse_ilias_search_page
from .ilias_feature_models import IliasInfoPage, IliasSearchFilters, IliasSearchPage
from .ilias_search_request import search_payload


def fetch_ilias_search_filters(client: IliasClient) -> IliasSearchFilters:
    response = client.session.get(
        ILIAS_SEARCH_URL,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    return extract_ilias_search_form(response.text, response.url).filters


def search_ilias(
    client: IliasClient,
    *,
    term: str,
    page: int = 1,
    search_mode: str | None = None,
    content_types: tuple[str, ...] = (),
    created_enabled: bool = False,
    created_mode: str | None = None,
    created_date: str | None = None,
) -> IliasSearchPage:
    normalized_term = term.strip()
    if not normalized_term:
        raise AlmaParseError("A non-empty ILIAS search term is required.")

    target_page = max(1, page)
    response = client.session.get(
        ILIAS_SEARCH_URL,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()

    contract = extract_ilias_search_form(response.text, response.url)
    payload = search_payload(contract, normalized_term, search_mode=search_mode, content_types=content_types,
                             created_enabled=created_enabled, created_mode=created_mode, created_date=created_date)
    response = client.session.post(
        contract.action_url,
        data=payload,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()

    current_page = parse_ilias_search_page(
        response.text,
        response.url,
        query=normalized_term,
        page_number=1,
    )
    while current_page.page_number < target_page:
        if current_page.next_page_url is None:
            raise AlmaParseError(f"ILIAS search does not expose page {target_page} for term '{normalized_term}'.")
        response = client.session.get(
            current_page.next_page_url,
            timeout=client.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        current_page = parse_ilias_search_page(
            response.text,
            response.url,
            query=normalized_term,
            page_number=current_page.page_number + 1,
        )

    return current_page


def fetch_ilias_info_page(client: IliasClient, *, target: str) -> IliasInfoPage:
    normalized_target = target.strip()
    if not normalized_target:
        raise AlmaParseError("A non-empty ILIAS info target is required.")

    if normalized_target.startswith(("http://", "https://")):
        info_url = normalized_target
    elif "cmd=infoScreen" in normalized_target:
        info_url = f"https://ovidius.uni-tuebingen.de/{normalized_target.lstrip('/')}"
    else:
        ref_match = re.search(r"(\d+)(?:/)?$", normalized_target)
        if ref_match is None:
            raise AlmaParseError("ILIAS info targets must be a full info URL or expose a numeric ref_id.")
        info_url = (
            "https://ovidius.uni-tuebingen.de/ilias.php"
            f"?baseClass=ilrepositorygui&cmd=infoScreen&ref_id={ref_match.group(1)}"
        )

    response = client.session.get(
        info_url,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    return parse_ilias_info_page(response.text, response.url)
