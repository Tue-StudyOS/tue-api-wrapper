from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from .advising_discovery_html import parse_discovery_page
from .advising_discovery_models import AdvisingDiscoveryError, AdvisingIndex
from .config import AlmaServiceUnavailableError

MAX_PAGES = 300
MAX_DEPTH = 2
WORKERS = 6


def crawl_advising(seeds: tuple[str, ...], fetcher: Callable, *, max_pages: int = MAX_PAGES,
                   max_depth: int = MAX_DEPTH) -> AdvisingIndex:
    pages, passages, errors = [], [], []
    attempted, queued, canonical = set(), set(seeds), set()
    current = [(url, None) for url in dict.fromkeys(seeds)]
    seed_links = set()
    seed_attempted = 0
    skipped, beyond_depth = set(), set()

    def read(item):
        url, parent = item
        try:
            html, final_url = fetcher(url)
            return parse_discovery_page(html, final_url, parent)
        except Exception as error:
            return AdvisingDiscoveryError(url, f'{type(error).__name__}: {error}')

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for depth in range(max_depth + 1):
            remaining = max(0, max_pages - len(attempted))
            selected, overflow = current[:remaining], current[remaining:]
            skipped.update(url for url, _ in overflow)
            following = []
            for item, result in zip(selected, pool.map(read, selected)):
                url, _ = item
                attempted.add(url)
                if depth == 1:
                    seed_attempted += 1
                if isinstance(result, AdvisingDiscoveryError):
                    errors.append(result)
                    continue
                page, entries, links = result
                if page.url in canonical:
                    continue
                canonical.add(page.url)
                pages.append(page)
                passages.extend(entries)
                for target, _context in links:
                    if target in queued or target in canonical:
                        continue
                    if depth == max_depth:
                        beyond_depth.add(target)
                        continue
                    queued.add(target)
                    following.append((target, page.url))
                    if depth == 0:
                        seed_links.add(target)
            if depth == 0:
                primary_error = next((error for error in errors if error.url == seeds[0]), None)
                if primary_error:
                    raise AlmaServiceUnavailableError(
                        f'The primary advising directory could not be loaded: {primary_error.message}'
                    )
            if overflow or not following:
                skipped.update(url for url, _ in following)
                break
            current = following
    return AdvisingIndex(
        refreshed_at=datetime.now(timezone.utc).isoformat(), pages=tuple(pages), passages=tuple(passages),
        errors=tuple(errors), pages_attempted=len(attempted), pages_skipped=len(skipped),
        links_beyond_depth=len(beyond_depth - queued - canonical), seed_links_discovered=len(seed_links),
        seed_links_attempted=seed_attempted,
    )
