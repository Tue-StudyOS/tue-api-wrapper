from __future__ import annotations

from .alma_account_html import parse_account_profile
from .alma_account_models import AlmaAccountProfile
from .client import AlmaClient
from .config import AlmaLoginError


def fetch_account_profile(client: AlmaClient) -> AlmaAccountProfile:
    response = client.session.get(
        client.start_page_url,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()
    if client._looks_logged_out(response.text):
        raise AlmaLoginError("Session is not authenticated; the Alma start page redirected back to login.")
    return parse_account_profile(response.text)
