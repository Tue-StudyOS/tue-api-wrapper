# Examples

These examples show the intended starting points for student projects.

Run them from the repository root after installing the package:

```bash
cd package
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[mcp]"
cd ..
```

## Python SDK

Public, unauthenticated data:

```bash
python examples/python_public_client.py
```

Authenticated data reads `UNI_USERNAME` and `UNI_PASSWORD` from `package/.env` or the shell:

```bash
python examples/python_authenticated_client.py
```

## MCP

Start the local MCP server:

```bash
cd package
tue mcp
```

Use `examples/mcp-client-config.json` as a template for editor or agent clients that accept MCP server JSON.

Run the Python stdio MCP client example:

```bash
python examples/mcp_stdio_client.py
```

The MCP examples keep credentials local. Public tools do not need a `.env`; authenticated tools do.
