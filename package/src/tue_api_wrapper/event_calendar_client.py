from __future__ import annotations

from datetime import timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import Element  # nosec B405

import requests

from .config import DEFAULT_TIMEOUT_SECONDS
from .event_calendar_models import UniversityCalendarEvent, UniversityCalendarResponse

UNIVERSITY_EVENTS_PAGE_URL = "https://uni-tuebingen.de/universitaet/campusleben/veranstaltungen/veranstaltungskalender/"
UNIVERSITY_EVENTS_FEED_URL = f"{UNIVERSITY_EVENTS_PAGE_URL}feed.xml"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
UTEVENT_NS = "{http://uni-tuebingen.de/ns/event/}"


def parse_university_events_feed(feed_xml: str, *, query: str = "", limit: int = 24) -> UniversityCalendarResponse:
    try:
        root = ET.fromstring(feed_xml)
    except (ET.ParseError, DefusedXmlException) as error:
        raise ValueError("University event feed was not valid XML.") from error

    channel = root.find("channel")
    if channel is None:
        raise ValueError("University event feed did not expose an RSS channel.")

    source_url = _node_text(channel, "link") or UNIVERSITY_EVENTS_PAGE_URL
    events = [_parse_item(item) for item in channel.findall("item")]
    events.sort(key=lambda item: item.starts_at)
    filtered = _filter_events(events, query=query)
    bounded_limit = min(max(1, limit), 100)
    returned = filtered[:bounded_limit]
    return UniversityCalendarResponse(
        source_url=source_url,
        feed_url=UNIVERSITY_EVENTS_FEED_URL,
        query=query,
        total_hits=len(filtered),
        returned_hits=len(returned),
        items=returned,
    )


class EventCalendarClient:
    def __init__(self, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    def fetch_events(self, *, query: str = "", limit: int = 24) -> UniversityCalendarResponse:
        response = requests.get(
            UNIVERSITY_EVENTS_FEED_URL,
            headers={"accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return parse_university_events_feed(response.text, query=query, limit=limit)


def _parse_item(item: Element) -> UniversityCalendarEvent:
    event_id = _node_text(item, "guid") or _node_text(item, "link") or _node_text(item, "title") or "event"
    starts_at = _parse_pub_date(_node_text(item, "pubDate"))
    return UniversityCalendarEvent(
        id=event_id,
        title=_node_text(item, "title") or "Untitled event",
        starts_at=starts_at,
        url=_node_text(item, "link"),
        speaker=_node_text(item, f"{UTEVENT_NS}speaker"),
        location=_node_text(item, f"{UTEVENT_NS}location"),
        description=_clean_text(_node_text(item, "description")),
        content_html=_clean_text(_node_text(item, f"{CONTENT_NS}encoded")),
        categories=[category for category in (_clean_text(node.text) for node in item.findall("category")) if category],
    )


def _node_text(node: Element, name: str) -> str | None:
    child = node.find(name)
    return _clean_text(child.text) if child is not None else None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = unescape(value).strip()
    return text or None


def _parse_pub_date(value: str | None) -> str:
    if not value:
        raise ValueError("University event feed item did not include a pubDate.")
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _filter_events(events: list[UniversityCalendarEvent], *, query: str) -> list[UniversityCalendarEvent]:
    needle = query.strip().lower()
    if not needle:
        return events
    return [event for event in events if needle in _event_haystack(event)]


def _event_haystack(event: UniversityCalendarEvent) -> str:
    text = "\n".join(
        [
            event.title,
            event.speaker or "",
            event.location or "",
            event.description or "",
            _strip_tags(event.content_html or ""),
            " ".join(event.categories),
        ]
    )
    return text.lower()


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)
