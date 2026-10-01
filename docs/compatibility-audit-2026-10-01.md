# Wrapper compatibility audit · 1 October 2026

Scope: failures reported in thread `019fb817-7054-7030-afb0-2dd48be773cf`,
current Python SDK/API behavior, and repository build/test coverage.
Checks used local credentials from `.env.local`; no university registration was performed.

## Confirmed fixes

- ALMA search previously converted a server validation failure into an empty result list.
  A timetable period ID such as `237` is not a search semester value. The live search
  form advertises `eq|31|2026` for Wintersemester 2026. Invalid values now raise
  `AlmaParseError` before submission, and rejected/unexpected responses raise errors.
- A search with only a semester previously ignored that semester. It now submits it.
- Successful ALMA search responses may contain the result table without the search form;
  validation accepts that actual response shape.
- ILIAS direct joining now handles the additional registration form documented in the
  source thread (`cdf_8073`, `cdf_8074`, `cdf_8075` for that particular course).
  These identifiers are parsed from the current form, never hardcoded into the client.
  Callers receive field labels and option values and supply `registration_values` explicitly.
  The helper validates selections and follows the fresh form action, with at most two posts.
- Unrelated membership text no longer counts as a confirmed course join. Direct-join
  result URLs omit the rotating request token.
- SDK and HTTP direct-join methods accept registration values. Existing calls remain valid.
- CI installs the new Python `dev` extra and runs pytest, covering both existing unittest
  cases and pytest tests. The previous install omitted pytest despite an existing test
  importing it; unittest discovery also omitted function-based tests.

## Verification

| Surface | Result |
| --- | --- |
| Python suite | 219 passed, 8 skipped; 3 subtests passed after integrating current main |
| Python compilation | Passed |
| Public live endpoint tests | 6 passed: seatfinder, TIMMS, canteen, events, talks, Praxisportal |
| ALMA live authenticated | Profile, timetable controls, planner, exams, exam reports, enrolments, documents, portal messages passed |
| ALMA live search | AIR and Virtual Humans each returned a result; nonexistent course returned zero; invalid period value reproduced server validation failure before fix |
| ILIAS live authenticated | Login, root, memberships, tasks, search filters and AIR search passed |
| Moodle live authenticated | Dashboard, categories, grades, messages, notifications passed; courses passed on retest after one remote connection closure |
| University mail | Authenticated mailbox listing passed |
| HTTP contract | OpenAPI generated 116 route paths; direct-join JSON request body verified; route forwarding regression passed |
| Desktop | Renderer and Electron builds passed |
| Next.js | Production build, lint/type checks and page generation passed |
| ChatGPT | Type check and build passed |
| Go | All tests, build and CLI help passed; build used Xcode's bundled Git directly to avoid the system Git license shim |

## Limits

- The new direct-join continuation was verified with focused regression tests based on
  the source thread's actual form. No live join, waitlist action or agreement acceptance
  was performed during this audit.
- iOS could not be built because Xcode requires license acceptance on this machine.
- Java could not be built because neither a Java runtime nor Gradle is installed.
- This is selected live integration coverage, not an exhaustive execution of every route.
  PPI's separate credentials, every course-specific content path, private document downloads,
  and mutation endpoints were not exercised live.
- Existing XML-as-HTML warnings remain in the ALMA portal-message tests.
- Repository changes were prepared for main. Installed connector bundles and deployed services were not updated.
  Dependency versions were not broadly upgraded.

## Reproduce the repository checks

```sh
cd package
pip install -e ".[dev]"
python -m pytest tests -q
TUE_API_LIVE_PUBLIC_TESTS=1 python -m pytest tests/test_public_endpoints_live.py -q
python -m compileall -q src
```

From the repository root, run `npm --prefix desktop run build`,
`npm --prefix nextjs run build`, `npm --prefix chatgpt run check`,
and `npm --prefix chatgpt run build`. In `go`, run `go test ./...` and
`go build ./cmd/tue` with a working Git executable on PATH.
