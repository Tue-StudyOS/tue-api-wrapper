---
name: tue-api-wrapper
description: Work on the Python clients, CLI, or native iOS app for University of Tübingen services.
---

# TUE API Wrapper

- `package/`: Python clients, parsers, local API and MCP servers, CLI, and tests.
- `ios/`: native Swift app and clients. Keep credentialed flows on device.
- `skills/tuebingen-university-workflows/`: agent workflow and service instructions.
- `docs/`: SDK, agent access, and observed university-service contracts.

Use existing typed clients and parsers. Keep files under 300 lines and preserve unrelated work. Do not introduce mock or fallback data. Surface errors clearly.

For an endpoint, find its client and parser in `package/src/tue_api_wrapper/`, update its typed contract, and add focused tests under `package/tests/`. Check whether the iOS client needs the same change. Run `cd package && python -m pytest tests -q` for Python changes; use `npm run build:ios` for the simulator app.
