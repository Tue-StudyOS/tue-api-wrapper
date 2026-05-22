# tue-api-wrapper

Python SDK, local API server, MCP tools, and app clients for University of Tuebingen study systems.

The project wraps live university systems such as Alma, ILIAS, Moodle, university mail, TIMMS, campus pages, and public course data. It does not ship mock data or replace those upstream systems. Public features work without credentials; private student features require credentials in your local process.

![CI](https://github.com/SebastianBoehler/tue-api-wrapper/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-Apache--2.0-D22128.svg)

## Install

Install the published Python package:

```bash
pip install tue-api-wrapper
```

Optional extras:

```bash
pip install "tue-api-wrapper[mcp]"
pip install "tue-api-wrapper[discovery]"
```

## Python Module Usage

Use `TuebingenPublicClient` for public data. It does not need a university login.

```python
from tue_api_wrapper import TuebingenPublicClient

client = TuebingenPublicClient()

modules = client.alma.search_modules("machine learning", max_results=10)
lectures = client.alma.current_lectures(date="02.05.2026", limit=20)
canteens = client.campus.canteens()
events = client.campus.events(query="KI", limit=10)
recordings = client.timms.search("theoretische informatik", limit=5)
```

Use `TuebingenAuthenticatedClient` for private student data. Credentials stay local to the Python process.

```python
import os
from tue_api_wrapper import TuebingenAuthenticatedClient

client = TuebingenAuthenticatedClient.login(
    username=os.environ["UNI_USERNAME"],
    password=os.environ["UNI_PASSWORD"],
)

timetable = client.alma.timetable("Sommer 2026")
documents = client.alma.studyservice_documents()
tasks = client.ilias.tasks()
deadlines = client.moodle.deadlines(days=30)
inbox = client.mail.inbox(limit=5)

client.close()
```

Credentials can also be loaded from `.env`:

```bash
UNI_USERNAME=your-zdv-id
UNI_PASSWORD=your-password
```

```python
from tue_api_wrapper import TuebingenAuthenticatedClient, UniversityCredentials

credentials = UniversityCredentials.from_env(".env")
client = TuebingenAuthenticatedClient(credentials)
```

## Common Methods

### Public Alma

```python
client.alma.search_modules("informatics", max_results=20)
client.alma.module_search_filters()
client.alma.module_detail(detail_url)
client.alma.current_lectures(date="02.05.2026", limit=20)
```

### Public Campus

```python
client.campus.canteens(menu_date="2026-05-07")
client.campus.canteen(611, menu_date="2026-05-07")
client.campus.buildings()
client.campus.building_detail("/einrichtungen/...")
client.campus.events(query="lecture", limit=24)
client.campus.gym_occupancy()
client.campus.kuf_occupancy()
client.campus.seat_availability()
```

### Public Directory, TIMMS, Talks, and Career Data

```python
client.directory.search("informatik")
client.timms.suggest("analysis", limit=8)
client.timms.search("theoretische informatik", offset=0, limit=20)
client.timms.item("item-id")
client.timms.streams("item-id")
client.timms.tree(node_id="root")
client.talks.search(query="AI", limit=16)
client.talks.item(123)
client.praxisportal.filters()
client.praxisportal.search(query="internship", per_page=20)
client.praxisportal.project(12345)
```

### Authenticated Alma

```python
client.alma.timetable("Sommer 2026")
client.alma.timetable_controls()
client.alma.timetable_view(term="Sommer 2026", limit=50)
client.alma.refresh_timetable_export_url(term="Sommer 2026")
client.alma.timetable_course_assignments("Sommer 2026", limit=20)
client.alma.current_lectures(date="02.05.2026", limit=50)
client.alma.course_offerings(query="data science", term="Sommer 2026")
client.alma.course_registration_support(detail_url)
client.alma.course_registration_options(detail_url)
client.alma.register_for_course(detail_url, planelement_id="...")
client.alma.catalog_page(term="Sommer 2026", limit=80)
client.alma.study_planner()
client.alma.portal_messages()
client.alma.exams()
client.alma.exam_reports()
client.alma.download_exam_report()
client.alma.enrollments()
client.alma.studyservice_documents()
client.alma.download_document(doc_id)
```

### Authenticated ILIAS

```python
client.ilias.root()
client.ilias.memberships()
client.ilias.tasks()
client.ilias.content(target)
client.ilias.forum_topics(target)
client.ilias.exercise_assignments(target)
client.ilias.search_filters()
client.ilias.search("algorithms", page=1)
client.ilias.info(target)
client.ilias.add_favorite(url)
client.ilias.waitlist_support(url)
client.ilias.join_waitlist(url, accept_agreement=True)
```

### Authenticated Moodle

```python
client.moodle.dashboard(event_limit=6, course_limit=12, recent_limit=9)
client.moodle.deadlines(days=30, limit=50)
client.moodle.courses(classification="all", limit=24, offset=0)
client.moodle.categories()
client.moodle.course(course_id)
client.moodle.enrol_in_course(course_id, enrolment_key=None)
client.moodle.grades()
client.moodle.messages()
client.moodle.notifications()
```

### Authenticated Mail and Portal

```python
client.mail.inbox(limit=12)
client.mail.mailbox(name="INBOX", limit=12, unread_only=False, query="")
client.mail.mailboxes()
client.mail.message(uid, mailbox="INBOX")

client.portal.dashboard(term="Sommer 2026", limit=8)
client.portal.search("seminar", term="Sommer 2026")
client.portal.item(item_id, term="Sommer 2026")
client.portal.course_detail(title="Machine Learning", term="Sommer 2026")
```

### Course Discovery

```python
client.discovery.search("machine learning", limit=20)
client.discovery.search(
    "seminar",
    sources=("alma", "ilias"),
    term="Sommer 2026",
    include_private=True,
)
client.discovery.refresh(include_private=True, limit=3000)
client.discovery.status()
```

## Local API Server

Start the FastAPI server:

```bash
tue-api-server
```

Useful URLs:

- API root: `http://127.0.0.1:8000/`
- health check: `http://127.0.0.1:8000/api/health`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

Public routes work without credentials. Authenticated routes read local credentials from environment variables such as `UNI_USERNAME` and `UNI_PASSWORD`.

## Feedback Issue Creation

The desktop, web, and iOS clients can create public GitHub feedback issues directly from the client without the local API server. Configure a fine-grained GitHub token with access to create issues in this repository:

- Desktop renderer builds read `VITE_GITHUB_FEEDBACK_TOKEN`.
- Next.js browser builds read `NEXT_PUBLIC_GITHUB_FEEDBACK_TOKEN`.
- iOS reads the `GITHUB_FEEDBACK_TOKEN` build setting into `GitHubFeedbackToken` in `Info.plist`.

If the token is missing, the feedback UI shows that issue creation is unavailable.

## Local MCP Server

Install the MCP extra and start the server:

```bash
pip install "tue-api-wrapper[mcp]"
tue-mcp
```

Use stdio for local agent clients. For HTTP clients:

```bash
tue-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `package/` | Python clients, parsers, SDK, FastAPI routes, MCP server, and tests |
| `java/` | Native Java/Android clients for upstream university systems |
| `nextjs/` | Next.js dashboard |
| `desktop/` | Electron desktop app with local credential handling |
| `ios/` | SwiftUI app and native client work |
| `chatgpt/` | ChatGPT app, MCP integration, and widget UI |
| `go/` | Go CLI experiments for stable request flows |
| `cli/` | Repo-local wrapper scripts |
| `docs/` | Discovery notes, release notes, SDK docs, and screenshots |
| `examples/` | Small example projects and usage snippets |

## Development

Run the checks that match your change:

```bash
cd package && pytest
cd java && gradle build
npm --prefix desktop run build
npm --prefix nextjs run build
npm run generate:ios
npm run build:ios
```

When adding integrations, start with the Python package, parse upstream responses into typed contracts, add focused tests, and expose shared JSON through FastAPI when app surfaces need it.

## Security

- Do not commit credentials, cookies, HAR files, signed URLs, PDFs, mailbox exports, or session artifacts.
- Keep authenticated flows local to the client or local backend.
- Do not route student credentials through hosted services.
- Prefer public data for teaching and demos unless private account data is required.
- Return clear errors for missing credentials or upstream failures.

## License

This repository is licensed under the Apache License 2.0. See [`LICENSE`](./LICENSE).
