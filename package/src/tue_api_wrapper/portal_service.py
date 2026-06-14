from __future__ import annotations

from typing import Any

from .client import AlmaClient
from .config import AlmaParseError, MailError
from .credentials import read_mail_credentials, read_uni_credentials
from .dashboard_builder import build_dashboard_payload
from .ilias_client import IliasClient
from .mail_client import MailClient
from .portal_cache import (
    PortalCache,
    clear_portal_cache,
    configure_portal_cache,
    credential_scope,
    default_portal_cache,
)
from .portal_common import DEFAULT_DASHBOARD_TERM, normalize_dashboard_term, serialize
from .portal_search import (
    build_dashboard_search_index,
    fetch_dashboard_index_item,
    search_dashboard_index,
)


class PortalService:
    """Authenticated portal facade with optional process-local in-memory caching.

    The built-in cache is intentionally small and local-only. It helps a local
    sidecar avoid duplicate upstream reads, but app-level deployments that need
    broader caching guarantees should own their own caching layer.
    """

    def __init__(self, cache: PortalCache | None = None) -> None:
        self._cache = cache or default_portal_cache()

    def _alma_client(self) -> AlmaClient:
        username, password = read_uni_credentials()
        if not username or not password:
            raise AlmaParseError(
                "Set UNI_USERNAME and UNI_PASSWORD before using authenticated endpoints. "
                "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
            )

        client = AlmaClient()
        client.login(username=username, password=password)
        return client

    def _ilias_client(self) -> IliasClient:
        username, password = read_uni_credentials()
        if not username or not password:
            raise AlmaParseError(
                "Set UNI_USERNAME and UNI_PASSWORD before using authenticated endpoints. "
                "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
            )

        client = IliasClient()
        client.login(username=username, password=password)
        return client

    def _mail_client(self) -> MailClient:
        username, password = read_mail_credentials()
        if not username or not password:
            raise MailError(
                "Set UNI_USERNAME and UNI_PASSWORD before using mail endpoints."
            )

        client = MailClient()
        client.login(username=username, password=password)
        return client

    def _mail_panel(self, *, limit: int = 6) -> dict[str, Any]:
        try:
            client = self._mail_client()
            try:
                inbox = client.fetch_inbox_summary(limit=limit)
            finally:
                client.close()
        except MailError as error:
            return {
                "available": False,
                "account": None,
                "mailbox": "INBOX",
                "unreadCount": 0,
                "items": [],
                "error": str(error),
            }

        return {
            "available": True,
            "account": inbox.account,
            "mailbox": inbox.mailbox,
            "unreadCount": inbox.unread_count,
            "items": serialize(inbox.messages),
            "error": None,
        }

    def build_dashboard(
        self,
        *,
        term_label: str = DEFAULT_DASHBOARD_TERM,
        limit: int = 8,
        include_course_assignments: bool = True,
    ) -> dict[str, Any]:
        normalized_term = normalize_dashboard_term(term_label)
        key = (
            "portal",
            "dashboard",
            *self._credential_scopes(),
            normalized_term,
            limit,
            include_course_assignments,
        )
        return self._cache.get_or_load(
            key,
            lambda: build_dashboard_payload(
                term_label=normalized_term,
                limit=limit,
                include_course_assignments=include_course_assignments,
                load_alma_client=self._alma_client,
                load_ilias_client=self._ilias_client,
                load_mail_panel=self._mail_panel,
            ),
        )

    def build_search_index(self, *, term_label: str = DEFAULT_DASHBOARD_TERM) -> list[dict[str, Any]]:
        normalized_term = normalize_dashboard_term(term_label)
        key = (
            "portal",
            "search_index",
            *self._credential_scopes(),
            normalized_term,
        )
        return self._cache.get_or_load(
            key,
            lambda: build_dashboard_search_index(
                self.build_dashboard(term_label=normalized_term, limit=12)
            ),
        )

    def search(self, query: str, *, term_label: str = DEFAULT_DASHBOARD_TERM) -> list[dict[str, Any]]:
        return search_dashboard_index(query, self.build_search_index(term_label=term_label))

    def fetch_item(self, item_id: str, *, term_label: str = DEFAULT_DASHBOARD_TERM) -> dict[str, Any]:
        return fetch_dashboard_index_item(item_id, self.build_search_index(term_label=term_label))

    def invalidate_portal_cache(self) -> None:
        self._cache.invalidate(prefix=("portal",))

    def _credential_scopes(self) -> tuple[str, str]:
        uni_username, uni_password = read_uni_credentials()
        mail_username, mail_password = read_mail_credentials()
        return (
            credential_scope("uni", uni_username, uni_password),
            credential_scope("mail", mail_username, mail_password),
        )


__all__ = [
    "DEFAULT_DASHBOARD_TERM",
    "PortalService",
    "clear_portal_cache",
    "configure_portal_cache",
    "normalize_dashboard_term",
    "serialize",
]
