from __future__ import annotations

from urllib.parse import quote

import requests

from .config import DEFAULT_TIMEOUT_SECONDS
from .hsp_html import hsp_offer_path, parse_hsp_course_search_data, parse_hsp_offer_page
from .hsp_models import HspCourseSearchResult, HspOfferPage

HSP_BASE_URL = "https://buchung.hsp.uni-tuebingen.de"
HSP_CURRENT_PROGRAM_URL = f"{HSP_BASE_URL}/angebote/aktueller_zeitraum"
HSP_COURSE_SEARCH_JS_URL = f"{HSP_CURRENT_PROGRAM_URL}/kurssuche.js"


class HspClient:
    def __init__(self, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    def search_courses(
        self,
        *,
        query: str = "",
        area: str | None = None,
        include_unavailable: bool = False,
        limit: int = 50,
    ) -> HspCourseSearchResult:
        response = requests.get(HSP_COURSE_SEARCH_JS_URL, timeout=self.timeout)
        response.raise_for_status()
        return parse_hsp_course_search_data(
            response.text,
            HSP_COURSE_SEARCH_JS_URL,
            query=query,
            area=area,
            include_unavailable=include_unavailable,
            limit=limit,
        )

    def fetch_offer(self, title: str) -> HspOfferPage:
        path = hsp_offer_path(title)
        url = f"{HSP_CURRENT_PROGRAM_URL}/{quote(path)}"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return parse_hsp_offer_page(response.text, response.url)
