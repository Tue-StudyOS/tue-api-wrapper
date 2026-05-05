from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..course_detail_linking import build_unified_course_detail, resolve_alma_course_detail
from ..dashboard_builder import build_dashboard_payload
from ..portal_common import DEFAULT_DASHBOARD_TERM, normalize_dashboard_term, serialize
from ..portal_search import build_dashboard_search_index, fetch_dashboard_index_item, search_dashboard_index


@dataclass(slots=True)
class AuthenticatedPortalApi:
    authenticated: Any

    def dashboard(
        self,
        *,
        term: str = DEFAULT_DASHBOARD_TERM,
        limit: int = 8,
        include_course_assignments: bool = True,
    ) -> dict[str, Any]:
        return build_dashboard_payload(
            term_label=normalize_dashboard_term(term),
            limit=limit,
            include_course_assignments=include_course_assignments,
            load_alma_client=lambda: self.authenticated.alma.client,
            load_ilias_client=lambda: self.authenticated.ilias.client,
            load_mail_panel=self._mail_panel,
        )

    def search(self, query: str, *, term: str = DEFAULT_DASHBOARD_TERM) -> list[dict[str, Any]]:
        return search_dashboard_index(query, self._search_index(term=term))

    def item(self, item_id: str, *, term: str = DEFAULT_DASHBOARD_TERM) -> dict[str, Any]:
        return fetch_dashboard_index_item(item_id, self._search_index(term=term))

    def course_detail(
        self,
        *,
        url: str = "",
        title: str = "",
        term: str = "",
        ilias_limit: int = 8,
    ):
        alma_client = self.authenticated.alma.client
        detail = resolve_alma_course_detail(
            alma_client,
            detail_url=url,
            title=title,
            term=term.strip() or None,
            search_client=alma_client if not url.strip() else None,
        )
        return build_unified_course_detail(
            detail,
            alma_client=alma_client,
            ilias_client=self.authenticated.ilias.client,
            moodle_client=self.authenticated.moodle.client,
            ilias_limit=ilias_limit,
        )

    def _search_index(self, *, term: str) -> list[dict[str, Any]]:
        return build_dashboard_search_index(self.dashboard(term=term, limit=12))

    def _mail_panel(self, *, limit: int = 6) -> dict[str, Any]:
        inbox = self.authenticated.mail.inbox(limit=limit)
        return {
            "available": True,
            "account": inbox.account,
            "mailbox": inbox.mailbox,
            "unreadCount": inbox.unread_count,
            "items": serialize(inbox.messages),
            "error": None,
        }
