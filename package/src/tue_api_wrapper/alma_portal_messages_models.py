from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AlmaPortalMessagesFeed:
    page_url: str
    feed_url: str | None
    can_refresh_feed: bool


@dataclass(frozen=True)
class AlmaPortalMessageItem:
    id: str
    title: str
    url: str | None
    target: str | None
    icon_url: str | None
    created_at: datetime | None
    created_at_label: str | None


@dataclass(frozen=True)
class AlmaPortalMessagesPage:
    page_url: str
    items: tuple[AlmaPortalMessageItem, ...]
