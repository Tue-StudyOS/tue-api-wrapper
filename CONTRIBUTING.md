# Contributing

Thanks for considering a contribution.

This repository mixes request-contract discovery, parsing, Python clients, local APIs, and CLI tooling. The best contributions are small, testable, and explicit about which contract or user-facing behavior they change.

## Before you start

Please read:

- [`README.md`](./README.md)
- [`LICENSE`](./LICENSE)
- [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- [`SECURITY.md`](./SECURITY.md)

If your change touches live Alma or ILIAS behavior, include enough context in the PR description for reviewers to understand what request flow or page shape changed.

## Ways to contribute

- fix a parser or login-flow regression
- add support for a new stable Alma or ILIAS endpoint
- add or improve fixture-based contract tests
- improve packaging, CI, or local developer ergonomics
- improve docs, onboarding, or examples

## License and contributor terms

This repository is open source under the Apache License 2.0.

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the project is provided under the Apache License 2.0 terms, as
described in Section 5 of [`LICENSE`](./LICENSE). No separate CLA is required
for normal pull requests.

## Development setup

### Python backend

```bash
cd package
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests -q
```

## Credentials and local data

- never commit usernames, passwords, cookies, HAR exports, PDFs, or signed URLs
- keep local credentials in ignored env files such as `.env.local`
- keep private debugging fixtures out of version control
- install the repository guard hook once per checkout:

```bash
git config core.hooksPath .githooks
```

## Change guidelines

Please try to keep PRs:

- focused on one logical change
- backed by tests or parser fixtures when behavior changes
- clear about expected JSON shape or user-facing output
- small enough to review without reconstructing unrelated context

When changing a contract:

- document the new endpoint or behavior
- add or update tests near the changed parser or client
- mention whether the flow was verified live, fixture-only, or both

## Route discovery

Use HAR imports only as local analysis inputs. Do not add HAR files to fixtures or commits.

To review whether a browser capture contains structured endpoints:

```bash
cd package
tue route-discovery generic --har ../local-session.har --audit-formats --format markdown
```

To restrict the audit to one host:

```bash
tue route-discovery generic --har ../local-session.har --audit-formats --start-url https://moodle.zdv.uni-tuebingen.de/my/
```

## PR checklist

Before opening a PR, please make sure:

- the relevant tests pass locally
- new behavior is documented when needed
- secrets and local artifacts are not included
- the PR description explains the problem, approach, and validation

Useful PR descriptions usually answer:

1. What broke or what capability was missing?
2. What contract or component changed?
3. How was the change validated?

## Review expectations

Review will generally focus on:

- correctness of the request or parsing contract
- regression risk
- test coverage
- maintainability and clarity
- handling of sensitive data

## Becoming a maintainer

Regular contributors who consistently land careful, well-tested changes are welcome to help with triage and review. See [`MAINTAINERS.md`](./MAINTAINERS.md) for the path and expectations.
