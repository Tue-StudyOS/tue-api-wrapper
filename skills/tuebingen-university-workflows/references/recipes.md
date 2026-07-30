# Local SDK and MCP recipes

Run private access only on the user's machine. Do not include credentials in code, logs, commits, screenshots, or agent messages.

## Public information

```python
from tue_api_wrapper import TuebingenPublicClient

client = TuebingenPublicClient()
modules = client.alma.search_modules("machine learning", max_results=10)
contacts = client.directory.search("informatics examination office")
recordings = client.timms.search("machine learning", limit=10)
```

Use public results to narrow a request before asking for private access.

## Local authenticated read

Create a local, gitignored `.env` with `UNI_USERNAME` and `UNI_PASSWORD`, then:

```python
from tue_api_wrapper import TuebingenAuthenticatedClient, UniversityCredentials

credentials = UniversityCredentials.from_env(".env")
client = TuebingenAuthenticatedClient(credentials)
try:
    timetable = client.alma.timetable_view(term="Winter 2026/27", limit=50)
    tasks = client.ilias.tasks()
    deadlines = client.moodle.deadlines(days=30, limit=50)
finally:
    client.close()
```

For a document, list first and download only the chosen item:

```python
reports = client.alma.exam_reports()
document = client.alma.download_exam_report(trigger_name="...")
# Write `document.content` only to the user-approved local destination.
```

Method names and return fields can change with upstream systems; inspect the installed package or current repository before adding application code.

## Registration preview and confirmation

```python
detail_url = "..."  # Select from an Alma course-offering result.
support = client.alma.course_registration_support(detail_url)
options = client.alma.course_registration_options(detail_url)
# Show support/options and ask for final confirmation.
result = client.alma.register_for_course(detail_url, planelement_id="...")
```

The final line is a mutation. Do not run it merely because a user asked to explore courses.

## Local MCP server

Install MCP support and run it locally:

```bash
pip install "tue-api-wrapper[mcp]"
tue-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

The MCP server exposes public Alma/course/event/TIMMS tools plus local authenticated timetable, ILIAS tasks, Moodle deadlines, mail summaries, and course discovery. Configure the MCP client to talk only to `127.0.0.1`; do not expose the credentialed server publicly.

## PPI exception

```python
from tue_api_wrapper import PpiClient

ppi = PpiClient()
try:
    ppi.login("zxabc12", "separate-ppi-password")
    catalog = ppi.fetch_lecture_catalog()
finally:
    ppi.close()
```

PPI uses its own password. Ask the user to configure it locally only for PPI tasks and confirm before borrowing a lecture or consuming a token.
