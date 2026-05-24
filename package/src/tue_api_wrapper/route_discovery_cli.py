from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urlparse

import requests

from .client import AlmaClient
from .config import AlmaError, AlmaParseError
from .credentials import read_uni_credentials
from .ilias_client import ILIAS_LOGIN_URL, ILIAS_ROOT_URL, IliasClient
from .route_discovery import discover_routes, discover_routes_from_har
from .route_discovery_audit import audit_har_response_formats, render_format_audit_markdown

DEFAULT_ALMA_START_URLS = (
    "https://alma.uni-tuebingen.de/alma/pages/cs/sys/portal/hisinoneStartPage.faces",
    "https://alma.uni-tuebingen.de/alma/pages/cm/exa/coursecatalog/showCourseCatalog.xhtml?_flowId=showCourseCatalog-flow&navigationPosition=studiesOffered%2CcourseoverviewShow&recordRequest=true",
    "https://alma.uni-tuebingen.de/alma/pages/cm/exa/curricula/moduleDescriptionSearch.xhtml?_flowId=searchElementsInModuleDescription-flow&navigationPosition=studiesOffered%2CmoduleDescriptions%2CsearchElementsInModuleDescription&recordRequest=true",
)
DEFAULT_ILIAS_START_URLS = (
    ILIAS_LOGIN_URL,
    ILIAS_ROOT_URL,
)


def _build_session(site: str, authenticated: bool) -> tuple[requests.Session, tuple[str, ...]]:
    if site == "generic":
        if authenticated:
            raise ValueError("site 'generic' does not support --auth. Use public start URLs or --har.")
        return requests.Session(), ()

    if site == "alma":
        client = AlmaClient()
        if authenticated:
            username, password = read_uni_credentials()
            if not username or not password:
                raise AlmaParseError(
                    "Set UNI_USERNAME and UNI_PASSWORD for authenticated crawling. "
                    "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
                )
            client.login(username=username, password=password)
            return client.session, (client.start_page_url, client.public_module_search_url)
        return client.session, DEFAULT_ALMA_START_URLS

    client = IliasClient()
    if authenticated:
        username, password = read_uni_credentials()
        if not username or not password:
            raise AlmaParseError(
                "Set UNI_USERNAME and UNI_PASSWORD for authenticated crawling. "
                "Legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks."
            )
        client.login(username=username, password=password)
        return client.session, (ILIAS_ROOT_URL,)
    return client.session, DEFAULT_ILIAS_START_URLS


def _render_markdown(report: dict[str, object], *, site: str, authenticated: bool, har_path: str | None) -> str:
    crawl_mode = f"HAR import (`{har_path}`)" if har_path else "live crawl"
    lines = [
        f"# {site.upper()} Route Discovery",
        "",
        f"- Mode: {crawl_mode}",
        f"- Authenticated crawl: {'yes' if authenticated else 'no'}",
        f"- Pages crawled: {len(report['pages'])}",
        f"- Unique routes: {len(report['routes'])}",
        f"- Forms detected: {len(report['forms'])}",
        "",
        "## Routes",
        "",
        "| Method(s) | Path | Query keys | Source(s) | Sample URL |",
        "| --- | --- | --- | --- | --- |",
    ]
    for route in report["routes"]:
        lines.append(
            "| "
            + ", ".join(route["methods"])
            + " | "
            + route["path"]
            + " | "
            + ", ".join(route["query_keys"])
            + " | "
            + ", ".join(route["sources"])
            + " | "
            + (route["sample_url"] or "")
            + " |"
        )

    lines.extend(["", "## Forms", ""])
    for form in report["forms"]:
        lines.extend(
            [
                f"### {form['method']} {form['action_url']}",
                f"- Seen on: {form['page_url']}",
                f"- Fields: {', '.join(form['field_names']) or '(none)'}",
                f"- Buttons: {', '.join(form['button_names']) or '(none)'}",
                "",
            ]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crawl Alma or ILIAS, or import a HAR, and report discovered routes, form actions, and field names.",
    )
    parser.add_argument(
        "site",
        choices=("alma", "ilias", "generic"),
        help="Target site to crawl. Use 'generic' for HAR imports or public non-Alma/ILIAS crawls.",
    )
    parser.add_argument("--auth", action="store_true", help="Use local credentials and crawl an authenticated session.")
    parser.add_argument("--har", help="Analyze a saved HAR file instead of making live requests.")
    parser.add_argument(
        "--audit-formats",
        action="store_true",
        help="For HAR imports, classify response formats and likely structured data endpoints.",
    )
    parser.add_argument("--depth", type=int, default=1, help="Maximum follow depth for discovered same-origin pages.")
    parser.add_argument("--max-pages", type=int, default=40, help="Maximum pages to crawl before stopping.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown", help="Output format.")
    parser.add_argument(
        "--start-url",
        action="append",
        default=[],
        help="Override the default start URLs. Can be passed multiple times.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.audit_formats:
            if not args.har:
                raise ValueError("--audit-formats requires --har.")
            start_urls = list(args.start_url)
            allowed_hosts = {urlparse(url).netloc for url in start_urls if urlparse(url).netloc} or None
            report = audit_har_response_formats(har_path=args.har, allowed_hosts=allowed_hosts)
        elif args.har:
            report = discover_routes_from_har(har_path=args.har)
            start_urls = list(args.start_url)
        else:
            session, default_start_urls = _build_session(args.site, args.auth)
            start_urls = list(tuple(args.start_url) or default_start_urls)
            if not start_urls:
                raise ValueError("No start URLs configured. Pass --start-url or use --har.")
            allowed_hosts = {urlparse(url).netloc for url in start_urls if urlparse(url).netloc}
            report = discover_routes(
                session=session,
                start_urls=start_urls,
                allowed_hosts=allowed_hosts,
                depth=max(0, args.depth),
                max_pages=max(1, args.max_pages),
                request_timeout=max(1, args.timeout),
            )
    except (AlmaError, ValueError) as error:
        print(f"route-discovery error: {error}", file=sys.stderr)
        return 1

    payload = {
        "site": args.site,
        "authenticated": args.auth,
        "har": args.har,
        "start_urls": start_urls,
        **report,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.audit_formats:
        print(render_format_audit_markdown(payload))
    else:
        print(_render_markdown(payload, site=args.site, authenticated=args.auth, har_path=args.har))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
