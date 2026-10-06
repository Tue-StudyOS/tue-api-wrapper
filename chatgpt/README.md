# Tübingen Study Hub plugin

An independent ChatGPT and Codex plugin for University of Tübingen students,
published by Sebastian Boehler. Support: s.boehler@student.uni-tuebingen.de.

The hosted service runs one Node 24 process with SQLite. It provides OAuth,
MCP, account links, confirmation records and an outbound device relay. Each
student runs the university API and sidecar on their own device. University
passwords and cookies stay there; requested study data passes through the
relay to ChatGPT. No separate identity service, Redis or external database is
required. Private tools return explicit errors when the device is unavailable.

## Features and UI

The server advertises 28 tools with output schemas, safety annotations and the
`study` OAuth scope. All existing study features remain in the first release.

| Feature | Tools | UI |
| --- | --- | --- |
| Connection | `get_connection_profile` | Account login and consent page; opaque profile ID |
| Unified search | `search`, `fetch` | Chat results with source links |
| Study overview | `get_study_snapshot`, `show_dashboard` | Compact inline summary; full dashboard on expansion |
| Schedule | `get_upcoming_schedule` | Agenda with dates and source links |
| Work and grades | `get_current_tasks`, `get_current_grades` | Task rows, exam rows and credit totals |
| Learning spaces | `get_learning_spaces`, `search_learning_spaces`, `inspect_learning_space` | Membership rows and content/forum/exercise detail |
| Courses | `get_course_catalog_filters`, `search_courses`, `search_course_offerings`, `get_course_detail`, `get_combined_course_detail`, `get_study_planner` | Search filters, course cards, detail sections and semester grid |
| Documents | `get_documents_summary`, `list_documents` | Document options and short-lived PDF download links |
| Mail | `get_mail_inbox`, `get_mail_message` | Inbox rows and selected plaintext message; no sending |
| Mensa | `get_mensa_food_plan` | Date/canteen/diet filters and meal rows |
| University actions | Four `prepare_*` tools, `confirm_critical_action`, `cancel_critical_action` | Preview with Proceed/Cancel; human Moodle key input |

University usage agreements must be read and accepted on the official website.
The model cannot accept an agreement or obtain a course key from chat. Each
confirmation belongs to one account, expires in ten minutes and can be consumed
once. A failed or uncertain submission is never retried automatically.

The widget uses the MCP Apps bridge with `window.openai` compatibility, host
themes, system typography, explicit error states and two inline actions. Full
navigation appears in fullscreen mode. See [design notes](DESIGN.md).

## Skills

The package contains [connection onboarding](skills/tuebingen-connect/SKILL.md)
and [browser recovery](skills/tuebingen-browser-recovery/SKILL.md). If a university
call fails, use available host browser/computer tools after the user signs in
on the official service. The plugin supplies instructions, not browser access.
If no browser tool is available, provide the official entry point and steps.

## Development

Use Node 24 or newer:

```sh
npm ci --workspaces=false
npm run check
npm test
npm run build
npm run dev
```

Development defaults to `http://127.0.0.1:8080`. HTTP is allowed only on loopback;
production requires an HTTPS `APP_BASE_URL`. A local student starts the Python
API, then runs:

```sh
npm run link-sidecar -- --server http://127.0.0.1:8080
```

The sidecar prints the link password for the account connection page. Its local
connection file is mode 0600. Never paste that password in chat. The Python API
normally runs on port 8000; `--backend http://127.0.0.1:8001` selects another local
port. `PORTAL_API_BASE_URL` is retained only for internal backend tests; HTTP MCP
requests always use the authenticated student's relay and never this variable.

## Deployment and submission

[Deployment instructions](DEPLOYMENT.md) cover a single VM with persistent SQLite
and Caddy TLS. [Submission instructions](SUBMISSION.md) describe the production
ZIP generator, reviewer access, public URLs and remaining external checks.
[Release review](RELEASE_REVIEW.md) records the implemented checks and their limits.
[Capacity measurements](CAPACITY.md) record the isolated small-container benchmark.

```sh
npm run release:package -- https://YOUR_PRODUCTION_HOST
```

Replace the hostname with the real production origin. The source manifest is
not an upload-ready MCP package; the generator fills the URLs and creates the
portable MCP configuration. Credentials and demo account access belong in the
secure review dashboard, never the ZIP. This repository has not been submitted
or deployed by this review.
