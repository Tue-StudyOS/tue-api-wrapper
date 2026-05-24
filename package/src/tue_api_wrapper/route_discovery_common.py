from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import parse_qsl, urljoin, urlparse

from bs4 import BeautifulSoup

ASSET_SUFFIXES = (
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".map",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
    ".xml",
)


@dataclass
class RouteArtifact:
    path: str
    query_keys: tuple[str, ...]
    methods: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
    sample_url: str | None = None
    sample_pages: set[str] = field(default_factory=set)


@dataclass
class FormArtifact:
    page_url: str
    action_url: str
    method: str
    field_names: tuple[str, ...]
    button_names: tuple[str, ...]


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = "&".join(f"{key}={value}" for key, value in parse_qsl(parsed.query, keep_blank_values=True))
    normalized = parsed._replace(fragment="", query=query)
    return normalized.geturl()


def route_key(url: str) -> tuple[str, tuple[str, ...]]:
    parsed = urlparse(url)
    query_keys = tuple(sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}))
    return parsed.path or "/", query_keys


def looks_html(url: str) -> bool:
    path = urlparse(url).path.lower()
    if not path:
        return True
    return not path.endswith(ASSET_SUFFIXES)


def should_follow(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in allowed_hosts:
        return False
    return looks_html(url)


def should_capture(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in allowed_hosts:
        return False
    return looks_html(url)


def collect_script_routes(soup: BeautifulSoup, page_url: str) -> list[str]:
    matches: list[str] = []
    pattern = re.compile(
        r"['\"]("
        r"(?:https?://[^'\"]+)"
        r"|(?:/(?:alma/|goto\.php/|ilias\.php|login\.php|shib_login\.php)[^'\"]*)"
        r"|(?:goto\.php/[^'\"]+)"
        r")['\"]"
    )
    for script in soup.find_all("script"):
        script_text = script.get_text(" ", strip=False)
        if not script_text:
            continue
        for match in pattern.finditer(script_text):
            candidate = urljoin(page_url, unescape(match.group(1)))
            matches.append(candidate)
    return matches


def extract_forms(soup: BeautifulSoup, page_url: str) -> list[FormArtifact]:
    artifacts: list[FormArtifact] = []
    for form in soup.find_all("form"):
        action = urljoin(page_url, form.get("action", page_url))
        method = form.get("method", "get").upper()
        field_names = sorted(
            {
                field.get("name", "").strip()
                for field in form.find_all(["input", "select", "textarea"])
                if field.get("name", "").strip()
            }
        )
        button_names = sorted(
            {
                button.get("name", "").strip()
                for button in form.find_all(["button", "input"])
                if button.get("name", "").strip()
                and (button.name == "button" or button.get("type") == "submit")
            }
        )
        artifacts.append(
            FormArtifact(
                page_url=page_url,
                action_url=action,
                method=method,
                field_names=tuple(field_names),
                button_names=tuple(button_names),
            )
        )
    return artifacts


def record_route(
    route_map: dict[tuple[str, tuple[str, ...]], RouteArtifact],
    *,
    url: str,
    method: str,
    source: str,
    page_url: str,
) -> None:
    path, query_keys = route_key(url)
    artifact = route_map.setdefault(
        (path, query_keys),
        RouteArtifact(path=path, query_keys=query_keys, sample_url=url),
    )
    artifact.methods.add(method.upper())
    artifact.sources.add(source)
    artifact.sample_pages.add(page_url)
    if artifact.sample_url is None:
        artifact.sample_url = url


def report_dict(
    pages: list[dict[str, object]],
    forms: list[FormArtifact],
    route_map: dict[tuple[str, tuple[str, ...]], RouteArtifact],
) -> dict[str, object]:
    route_rows = [
        {
            "path": artifact.path,
            "query_keys": list(artifact.query_keys),
            "methods": sorted(artifact.methods),
            "sources": sorted(artifact.sources),
            "sample_url": artifact.sample_url,
            "sample_pages": sorted(artifact.sample_pages)[:3],
        }
        for artifact in sorted(route_map.values(), key=lambda item: (item.path, item.query_keys))
    ]
    form_rows = [
        {
            "page_url": artifact.page_url,
            "action_url": artifact.action_url,
            "method": artifact.method,
            "field_names": list(artifact.field_names),
            "button_names": list(artifact.button_names),
        }
        for artifact in forms
    ]
    return {
        "pages": pages,
        "routes": route_rows,
        "forms": form_rows,
    }


def extract_html_page(
    *,
    html: str,
    page_url: str,
    status_code: int | None,
    allowed_hosts: set[str],
    forms: list[FormArtifact],
    route_map: dict[tuple[str, tuple[str, ...]], RouteArtifact],
) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None

    for link in soup.find_all("a", href=True):
        discovered_url = normalize_url(urljoin(page_url, link["href"]))
        if should_capture(discovered_url, allowed_hosts):
            record_route(route_map, url=discovered_url, method="GET", source="link", page_url=page_url)

    page_forms = extract_forms(soup, page_url)
    forms.extend(page_forms)
    for form_artifact in page_forms:
        normalized_action_url = normalize_url(form_artifact.action_url)
        if should_capture(normalized_action_url, allowed_hosts):
            record_route(
                route_map,
                url=normalized_action_url,
                method=form_artifact.method,
                source="form",
                page_url=page_url,
            )

    for discovered_url in collect_script_routes(soup, page_url):
        normalized = normalize_url(discovered_url)
        if should_capture(normalized, allowed_hosts):
            record_route(route_map, url=normalized, method="GET", source="script", page_url=page_url)

    page: dict[str, object] = {"url": page_url, "title": title}
    if status_code is not None:
        page["status"] = status_code
    return page
