from __future__ import annotations

from dataclasses import dataclass

from .advising_models import AdvisingLink


@dataclass(frozen=True)
class AdvisingPassage:
    source_url: str
    page_title: str
    section: str
    kind: str
    text: str
    links: tuple[AdvisingLink, ...]


@dataclass(frozen=True)
class AdvisingDiscoveryPage:
    url: str
    title: str
    discovered_from: str | None


@dataclass(frozen=True)
class AdvisingDiscoveryError:
    url: str
    message: str


@dataclass(frozen=True)
class AdvisingSearchResponse:
    query: str
    pages: tuple[AdvisingDiscoveryPage, ...]
    results: tuple[AdvisingPassage, ...]
    errors: tuple[AdvisingDiscoveryError, ...]
    pages_skipped: int
    results_truncated: bool
    refreshed_at: str
    pages_attempted: int
    links_beyond_depth: int
    seed_links_discovered: int
    seed_links_attempted: int


@dataclass(frozen=True)
class AdvisingIndex:
    refreshed_at: str
    pages: tuple[AdvisingDiscoveryPage, ...]
    passages: tuple[AdvisingPassage, ...]
    errors: tuple[AdvisingDiscoveryError, ...]
    pages_attempted: int
    pages_skipped: int
    links_beyond_depth: int
    seed_links_discovered: int
    seed_links_attempted: int
