"""Get ILIAS search responses without parsing the result page."""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from .config import AlmaParseError
from .ilias_feature_html import ILIAS_SEARCH_URL, extract_ilias_search_form
from .ilias_search_request import search_payload


def fetch_raw_ilias_search(client, *, query: str = "", form_only: bool = False) -> dict:
    if not form_only and not query.strip():
        raise ValueError("A search query is required")
    response = client.session.get(ILIAS_SEARCH_URL, timeout=client.timeout_seconds, allow_redirects=False)
    stage = "form"
    if not form_only and 200 <= response.status_code < 300:
        form = extract_ilias_search_form(response.text, response.url)
        action = urlparse(form.action_url)
        expected = urlparse(ILIAS_SEARCH_URL)
        params = {key.casefold(): [v.casefold() for v in values] for key, values in parse_qs(action.query).items()}
        if (action.scheme != "https" or action.netloc != expected.netloc or action.path != "/ilias.php"
                or params.get("baseclass") != ["ilsearchcontrollergui"]
                or params.get("cmd") != ["post"] or params.get("fallbackcmd") != ["performsearch"]):
            raise AlmaParseError("ILIAS search form has an unexpected action URL")
        response = client.session.post(form.action_url, data=search_payload(form, query),
                                       timeout=client.timeout_seconds, allow_redirects=False)
        stage = "results"
    return {"service": "ilias", "stage": stage, "status_code": response.status_code,
            "request_url": response.url, "content_type": response.headers.get("Content-Type"),
            "location": response.headers.get("Location"), "body": response.text, "redirects_followed": False}
