# tue-api-wrapper Python package

Python SDK, FastAPI server, and local MCP server for University of Tübingen study systems.

The package has three entry points:

- `TuebingenPublicClient`: public data that does not need credentials
- `TuebingenAuthenticatedClient`: private university data with explicit credentials
- `tue-mcp`: local MCP server for agents and LLM tools

## Install for local development

```bash
cd package
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install MCP support when you want the agent server:

```bash
pip install -e ".[mcp]"
```

## Public data example

```python
from tue_api_wrapper import TuebingenPublicClient

client = TuebingenPublicClient()

modules = client.alma.search_modules("machine learning", max_results=10)
events = client.campus.events(query="AI", limit=5)
gym = client.campus.gym_occupancy()
canteens = client.campus.canteens()
recordings = client.timms.search("theoretische informatik", limit=5)
```

## Authenticated data example

Load credentials with the standard Python environment API and pass them explicitly:

```python
import os
from tue_api_wrapper import TuebingenAuthenticatedClient

client = TuebingenAuthenticatedClient.login(
    username=os.environ["UNI_USERNAME"],
    password=os.environ["UNI_PASSWORD"],
)

profile = client.alma.profile()
timetable = client.alma.timetable("Sommer 2026")
documents = client.alma.studyservice_documents()
tasks = client.ilias.tasks()
deadlines = client.moodle.deadlines(days=30)
inbox = client.mail.inbox(limit=5)
```

In a local shell:

```bash
export UNI_USERNAME=your-zdv-id
export UNI_PASSWORD=your-password
```

## Course search and ILIAS registration

ALMA course search uses the exact values returned by `course_offerings().term_options`:

```python
terms = client.alma.course_offerings().term_options
courses = client.alma.course_offerings(query="Advanced Information Retrieval", term="eq|31|2026")
```

Search semester values differ from timetable/catalogue period IDs (`237`, for example).
Invalid values and rejected search forms raise `AlmaParseError` instead of returning an empty course list.
A semester without a query also submits a search.

Inspect direct ILIAS registration with `client.ilias.course_join_support(url)`.
`client.ilias.join_course(url, accept_agreement=True)` can return `requires_input` with
`registration_fields`: field names, labels, and the available option values. Supply those
exact values through `registration_values={...}` after reviewing the requested study details.
The helper handles the additional form step and uses its fresh action URL internally.
Agreement acceptance and study details must be supplied explicitly; they are never inferred.

The HTTP equivalent is `POST /api/ilias/course-join?url=...&accept_agreement=true`,
with a JSON object mapping registration field names to values as the request body.
A `submitted` result is unconfirmed; only explicit membership confirmation produces `joined`.

Run tests with `python -m pytest tests -q`. Enable the public live smoke tests with
`TUE_API_LIVE_PUBLIC_TESTS=1 python -m pytest tests/test_public_endpoints_live.py -q`.

## PPI exam protocols

PPI has its own account and password. Do not pass your university/ZDV password to it.

```python
from tue_api_wrapper import PpiClient

ppi = PpiClient()

# Creates a PPI account and sends an activation link to the corresponding
# <ZDV username>@student.uni-tuebingen.de mailbox.
signup = ppi.signup("zxabc12", "a-separate-ppi-password")

ppi.login("zxabc12", "a-separate-ppi-password")
catalog = ppi.fetch_lecture_catalog()
borrowed = ppi.fetch_borrowed_lectures()
lecture = next(item for item in borrowed.lectures if item.download_available and item.id is not None)
archive = ppi.download_lecture(lecture.id)
ppi.close()
```

The local API server reads `PPI_USERNAME` and `PPI_PASSWORD` for authenticated
PPI routes. Signup uses `POST /api/ppi/signup`; catalog, borrowing, downloads,
and token requests are available below `/api/ppi/`.

## Local MCP server

```bash
cd package
pip install -e ".[mcp]"
tue-mcp
```

Use `stdio` for most local agent clients. For HTTP-based clients:

```bash
tue-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

## FastAPI server

```bash
tue-api-server
```

The API starts on `http://127.0.0.1:8000` and exposes OpenAPI docs at `/docs`.

## Publishing

Install the published package from [PyPI](https://pypi.org/project/tue-api-wrapper/):

```bash
pip install tue-api-wrapper
```

Install with MCP extras:

```bash
pip install "tue-api-wrapper[mcp]"
```

You can also install directly from GitHub:

```bash
pip install "tue-api-wrapper @ git+https://github.com/SebastianBoehler/tue-api-wrapper.git#subdirectory=package"
```

MCP extras from GitHub:

```bash
pip install "tue-api-wrapper[mcp] @ git+https://github.com/SebastianBoehler/tue-api-wrapper.git#subdirectory=package"
```

Release steps live in [`../docs/release-pypi.md`](../docs/release-pypi.md).

## More docs

- [`../docs/python-sdk.md`](../docs/python-sdk.md)
- [`../docs/mcp.md`](../docs/mcp.md)
- [`../docs/release-pypi.md`](../docs/release-pypi.md)
- [`../examples/`](../examples/)
- [`../README.md`](../README.md)
