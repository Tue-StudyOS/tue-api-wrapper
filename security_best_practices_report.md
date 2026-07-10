# Security review — 2026-07-10

## Executive summary

The reported Python-package blocker is fixed: `tue-api-wrapper` 0.2.3 now requires Pillow 12.3+, the latest stable release at review time and newer than the 12.2 security-fix floor. Fresh `pip-audit` scans of the core package and both optional extras found no known vulnerabilities.

This was a dependency-focused review with a few low-risk hardening fixes, not a full authentication or deployment redesign. JavaScript lockfiles were updated where patched versions were available. One moderate transitive PostCSS advisory remains inside Next.js because Next 15.5.20 still pins PostCSS 8.4.31 and `npm audit` offers no safe in-major remediation.

## Fixed findings

### SEC-001 — Vulnerable Pillow constraint

- Rule ID: FASTAPI-SUPPLY-001
- Severity: High
- Location: `package/pyproject.toml:7,24-32`
- Evidence: the previous `pillow>=10.4,<12` constraint resolved Pillow 11.3.0, for which `pip-audit` reported five distinct 2026 CVEs and a highest fixed floor of 12.2.0.
- Impact: crafted image input could reach known vulnerable Pillow decoder paths.
- Fix: require `pillow>=12.3,<13`, bump the package to 0.2.3, and verify the installed runtime reports Pillow 12.3.0.
- Mitigation: `package/src/tue_api_wrapper/fitness_client.py:52-64` now rejects unexpectedly large images before decoding pixel data.
- False positive notes: none; the vulnerable version was reproduced by dependency resolution before the fix.

### SEC-002 — Entity-capable XML parsing

- Rule ID: PYTHON-XML-001
- Severity: Medium
- Location: `package/src/tue_api_wrapper/alma_partial.py:3-15`, `package/src/tue_api_wrapper/alma_portal_messages_html.py:6-7,174-177`, `package/src/tue_api_wrapper/alma_portal_messages_items_html.py:7-8,65-71`, `package/src/tue_api_wrapper/event_calendar_client.py:7-9,22-26`
- Evidence: upstream XML responses were parsed with `xml.etree.ElementTree.fromstring`.
- Impact: malicious or compromised upstream XML could attempt entity-expansion denial of service.
- Fix: use `defusedxml` and normalize rejected declarations into the existing parser errors.
- Mitigation: regression tests cover entity declarations in all affected parser paths.
- False positive notes: the upstreams are expected to be trusted university services, which reduces likelihood but not parser exposure.

### SEC-003 — Local API listened on every interface by default

- Rule ID: FASTAPI-DEPLOY-001
- Severity: Medium
- Location: `package/src/tue_api_wrapper/api_server.py:263-269`, `package/Dockerfile:10-11`
- Evidence: the package entry point previously hard-coded `0.0.0.0` even though authenticated clients use environment-backed student credentials.
- Impact: a locally started API could be reachable from other hosts on the same network.
- Fix: default the package entry point to `127.0.0.1`; the container explicitly opts into `0.0.0.0` where container networking requires it.
- Mitigation: keep credentialed deployments private and single-user as documented.
- False positive notes: container exposure remains deployment-dependent and was intentionally preserved.

## Remaining dependency advisory

### SEC-004 — Next.js-bundled PostCSS 8.4.31

- Rule ID: JS-SUPPLY-001
- Severity: Medium
- Location: `nextjs/package.json:17,30`, `nextjs/package-lock.json:4401-4411,4462-4464`
- Evidence: Next.js 15.5.20 declares an exact dependency on PostCSS 8.4.31; `npm audit` reports GHSA-qx2v-qp2m-jg93 through that nested copy.
- Impact: the advisory concerns unsafe CSS stringification; practical exposure is lower here because this copy is used by the trusted application build rather than to stringify user-supplied CSS at runtime.
- Fix: no safe automatic fix is currently offered. The direct PostCSS dependency is 8.5.16 and Next.js was updated from 15.5.12 to 15.5.20 to clear its high-severity advisories.
- Mitigation: do not process untrusted CSS with the Next build pipeline; update Next when its stable line moves off PostCSS 8.4.31.
- False positive notes: `npm audit --force` proposes an invalid downgrade to Next 9.3.3, so it was not applied.

## Verification

- Python: 177 tests passed, 8 live/optional tests skipped; compileall passed.
- Package audit: core and `mcp,discovery` extras reported no known vulnerabilities.
- Static scan: no high-severity Bandit findings after remediation.
- JavaScript: ChatGPT and Desktop audits reported zero vulnerabilities; Next.js/root retain only SEC-004.
- Builds: Next.js, ChatGPT, and Desktop production builds passed.
