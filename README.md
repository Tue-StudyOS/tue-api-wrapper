# Tübingen API wrapper

Python clients and a native Swift iOS app for University of Tübingen services. This independent project is not an official university application.

## Python client and CLI

```bash
cd package
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mcp]"
tue --help
tue study --help
```

The single `tue` command groups the existing tools. Use `tue <command> --help` for arguments. For example, `tue study connectivity` checks service reachability, `tue mcp` starts the local agent server, and `tue api-server` starts the local HTTP API. The API server uses `HOST` and `PORT` environment variables and defaults to loopback.

See the [Python package guide](package/README.md), [SDK reference](docs/python-sdk.md), and [examples](examples/README.md). Run the Python tests with `cd package && python -m pytest tests -q`.

## Agent access

The [university workflows skill](skills/tuebingen-university-workflows/SKILL.md) explains how an agent finds and uses services. The [course access guide](docs/agent-course-access.md) describes request contracts and their limits. The [MCP guide](docs/mcp.md) covers local tool setup and service selection. These contracts reflect observed behavior and can change upstream.

Public services need no credentials. For private services, set `UNI_USERNAME` and `UNI_PASSWORD` locally; never paste passwords into a conversation or send them to a hosted wrapper. The PPI service uses separate credentials. Treat registration, submission, and other writes as explicit actions and check the resulting service state.

## iOS app

The [iOS guide](ios/README.md) covers the native app and its build requirements. Generate and build the simulator app with `npm run build:ios`. The app keeps credentials on the device for its native authenticated flows.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). The code is licensed under [Apache 2.0](LICENSE).
