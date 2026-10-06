# Release review

## Code prepared

- One Node 24 service with SDK OAuth routes, PKCE S256, resource checks, `study`
  scope enforcement, hashed opaque tokens, rotation and revocation.
- Stable opaque account profile and student-specific outbound local sidecar.
  Hosted requests cannot fall through to a shared university backend.
- SQLite-backed, account-bound confirmations with atomic single-use consumption.
  Preparation and cancellation do not submit a university change. Restarts
  preserve pending intents; uncertain submissions require checking the portal.
- Human Moodle course-key input in the confirmation widget. University agreements
  are accepted on the university website before a waitlist action is prepared.
- Single-use private PDF capabilities, two-minute expiry, owner-specific delivery,
  size/type checks and no stored PDF data.
- All original tools plus the connection profile: 28 schemas, explicit safety
  hints, OAuth metadata and widget resource links. Both browser recovery and
  connection onboarding skills are packaged.
- Python/TypeScript current-semester handling follows the university's April and
  October boundaries in Europe/Berlin. Parent exam aggregates no longer duplicate
  leaf credits; missing and malformed records are handled explicitly.
- Compact inline overview with two actions; fullscreen feature navigation, host
  theme tokens, system typography, responsive spacing and explicit retry/errors.
- Public publisher, support, privacy and terms pages. Publisher: Sebastian Boehler;
  support: s.boehler@student.uni-tuebingen.de. Original icon, eight review cases,
  deployment instructions and a production ZIP generator with real-URL checks.
- Pinned MCP dependencies and a lockfile; Node 24 CI, regression tests and build.

## Verification and limits

Local Node 24 protocol tests cover OAuth metadata and login, CSRF, PKCE failures,
wrong audiences and redirects, code replay, refresh rotation, scope escalation,
revocation, disconnect, authenticated MCP, account isolation, persistence across
restart, action replay, private downloads and release metadata. Existing tests
cover sanitized HTTP errors, tool failures/output contracts, action preparation,
cancellation and confirmation, widget messaging, host appearance and display mode.

Python tests cover grade aggregation, current-semester boundaries and timetable
contract variants. Tests use labeled fixture servers only; the production code
contains no demo data or portal error fallback. The installed global Python
pytest plugin set is incompatible with pytest, so targeted tests run with
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src`.

Final verification: **73 Node 24 tests passed; 229 Python tests passed and eight
were skipped**. Type checking, production build, Docker build, hardened container
smoke checks, Compose/Caddy validation and production package generation with a
temporary test origin passed. npm audit reported zero known vulnerabilities.
The generated test ZIP was inspected for credentials and unintended files.
See [capacity results](CAPACITY.md) for the bounded 30/60-reader protocol runs.

The widget bundle is 60,512 bytes of minified JavaScript and CSS, about 19% below
its original 74,712-byte combined size. This is transfer size, not a browser
render-time or upstream latency benchmark. Browser previews checked light/dark
and inline/fullscreen layouts with labeled fixture data. Real ChatGPT iframe
behavior and live private university sessions still need deployed validation.

## External release checks

The code is prepared for single-VM deployment and production packaging. Public
release still requires a VM, HTTPS origin, publisher/domain verification, real
student and reviewer account execution, a recorded walkthrough, and public
integration eligibility. University authorization or an OpenAI policy exception
has not been established. Do not describe the integration as university-approved.
The generator cannot produce the actual production package before its real URL
exists. Dashboard credentials and video are deliberately absent from the ZIP.

Load-test the deployed VM and measure real private portal latency before claiming
capacity or reliability. Two real accounts must verify separation. Reviewers must
have a working demo account with no additional device setup or MFA; its authorized
sidecar remains running on the operator's own machine during review. No private
portal mutation or public submission happened in these local tests.

Official guidance used: [auth](https://developers.openai.com/plugins/build/auth),
[UI design](https://developers.openai.com/plugins/concepts/ui-guidelines),
[packaging](https://developers.openai.com/plugins/build/plugins),
[submission](https://developers.openai.com/plugins/deploy/submission),
[guidelines](https://developers.openai.com/plugins/plugin-guidelines).
The official OpenAI Developers build/submission skill sources and official
skill-creator skill guided preparation; Plugin Creator was not connected here.
