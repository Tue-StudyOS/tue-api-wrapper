"""Retrieve Alma search HTML without parsing search results."""
from __future__ import annotations

from urllib.parse import parse_qs, urljoin, urlparse

from .alma_course_search_html import COURSE_SEARCH_URL, extract_course_search_form
from .config import AlmaParseError


def fetch_raw_alma_search(client, *, query: str = "", term: str | None = None, form_only: bool = False):
    response = client.session.get(COURSE_SEARCH_URL, timeout=client.timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    if urlparse(response.url).hostname != urlparse(COURSE_SEARCH_URL).hostname:
        raise AlmaParseError("Alma search redirected outside the Alma host")
    if not form_only:
        if not query.strip():
            raise ValueError("A search query is required")
        form = extract_course_search_form(response.text, response.url)
        if term is not None and term not in {option.value for option in form.term_options}:
            raise AlmaParseError("Invalid Alma search term; use a value from term_options")
        if urlparse(form.action_url).netloc != urlparse(response.url).netloc:
            raise AlmaParseError("Alma search form action has an unexpected host")
        payload = dict(form.payload)
        payload[form.query_field_name] = query.strip()
        if term is not None:
            payload[form.term_field_name] = term
        payload["activePageElementId"] = form.search_button_name
        payload[form.search_button_name] = "Suchen"
        response = client.session.post(form.action_url, data=payload, timeout=client.timeout_seconds, allow_redirects=False)
        response = _follow_search_redirects(client, response)
    return {"service": "alma", "stage": "form" if form_only else "results", "status_code": response.status_code,
            "request_url": response.url, "content_type": response.headers.get("Content-Type"),
            "location": response.headers.get("Location"), "body": response.text}


def _follow_search_redirects(client, response):
    for _ in range(3):
        if response.status_code not in {301, 302, 303} or not response.headers.get("Location"):
            return response
        source = urlparse(response.url)
        target = urlparse(urljoin(response.url, response.headers["Location"]))
        source_flow = parse_qs(source.query).get("_flowId")
        target_flow = parse_qs(target.query).get("_flowId")
        if (target.scheme != "https" or target.netloc != source.netloc or target.path != source.path
                or not source_flow or target_flow != source_flow):
            raise AlmaParseError("Alma search returned an unexpected redirect")
        response = client.session.get(target.geturl(), timeout=client.timeout_seconds, allow_redirects=False)
    if response.status_code in {301, 302, 303}:
        raise AlmaParseError("Alma search returned too many redirects")
    return response
