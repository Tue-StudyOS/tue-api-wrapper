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
pip install -e .
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
