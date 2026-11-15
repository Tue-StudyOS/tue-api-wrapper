# University Auth Migration Design

Historical design: its hosted credential-vault and Cloud Run prototype proposals
are superseded by [authentication boundaries](../../authentication-boundaries.md).
Do not use those proposals as authorization to collect ZDV passwords in a hosted service.

## Context

The project currently has three credential surfaces:

- The iOS app stores university credentials in Keychain and already uses them for Alma schedule lookups and on-device IMAP mail.
- The Python backend still reads `UNI_USERNAME` / `UNI_PASSWORD` from its environment for Moodle, ILIAS, Alma registration, grades, dashboard, and ChatGPT-facing tools.
- The ChatGPT app is an unauthenticated MCP server that calls the env-backed backend.

This works for a single developer account, but it does not work for production multi-user use. A user's iOS Keychain credentials do not configure the backend, and hardcoded backend credentials cannot represent multiple students.

## Design Goals

- Private university data must be fetched with the current user's credentials, not a shared backend credential.
- The iOS app should execute Alma, Moodle, ILIAS, and mail requests on-device using Keychain credentials whenever the target portal supports direct HTTPS access.
- Backend authenticated routes remain available only as legacy/dev compatibility surfaces until they are replaced.
- ChatGPT private-data tools must use Apps SDK authentication instead of storing university credentials in widget `localStorage`, cookies, or `widgetState`.
- The migration must be incremental: every step should keep the app buildable and testable.

## Non-Goals

- Do not build a watch complication or desktop/menu bar companion in this migration.
- Do not transmit raw university credentials to the Python backend per request, even if encrypted at the transport layer.
- Do not add fallback or mock data. Missing credentials and portal failures should be explicit user-facing errors.
- Do not replace public Alma catalog/module search endpoints; those can remain unauthenticated backend calls.

## Approaches Considered

### Recommended: On-Device iOS Clients + OAuth ChatGPT

Port private portal fetches into small Swift clients under `ios/Shared/University`, backed by the existing Keychain credential store. Keep public/search backend routes unchanged. Mark env-backed backend private routes as legacy/dev and move iOS screens off them one feature at a time. For ChatGPT, add OAuth 2.1/PKCE-protected MCP access and a server-side encrypted credential-linking flow only for users who opt into ChatGPT private data.

This is the right shape because it removes shared backend credentials from the iOS path immediately and matches the Apps SDK expectation that user-specific or write-capable apps authenticate users.

### Alternative: Encrypted Credentials Per Backend Request

The app could encrypt credentials client-side and pass them to the backend on each request. This avoids backend env secrets but still centralizes raw credential handling on the server, increases breach impact, complicates key management, and makes every request sensitive. This is not selected.

### Alternative: Backend User Accounts Only

The backend could become the only authenticated surface, with every iOS and ChatGPT request using backend accounts. This gives one auth model but delays iOS privacy improvements and creates a larger credential vault before we have proof that each portal workflow works on-device. This is not selected for the first migration slice.

## iOS Architecture

Add a small on-device university access layer:

- `UniversityPortalClient`: high-level facade that loads credentials and runs selected private portal calls.
- `IliasOnDeviceClient`: logs into ILIAS through the university IdP and fetches the derived task overview.
- `MoodleOnDeviceClient`: logs into Moodle through Shibboleth and fetches calendar deadlines through Moodle's AJAX endpoint.
- `UniversityHTMLFormParser`: shared parser for Shibboleth forms, hidden SAML handoff forms, and IdP error messages.
- `IliasTaskHTMLParser` and `MoodleCalendarNormalizer`: tested parsers for portal payloads.

`AppModel.refreshTasks()` should use `UniversityPortalClient` and only show a missing-credentials error if Keychain has no saved credentials. It should no longer depend on `BackendClient.fetchIliasTasks()` or `BackendClient.fetchMoodleCalendar()`.

Grades should move later through the same pattern: Alma exam records and Moodle grades should become on-device calls, then `GradeOverviewView` can stop calling backend grade endpoints.

## Backend Legacy/Dev Policy

Routes that require `UNI_USERNAME` / `UNI_PASSWORD` remain available for local development, Cloud Run prototypes, and ChatGPT until OAuth migration lands. They must be documented and described as legacy/dev-authenticated, not production multi-user endpoints.

Public endpoints that do not need credentials can remain backend routes:

- Public Alma module search and module detail.
- Public talks and campus discovery.
- Static or derived metadata that does not expose one user's private account.

## ChatGPT App Auth Design

The ChatGPT app is a `tool-only` plus widget MCP app today. For private university data, it needs an authenticated MCP server.

Based on the OpenAI Apps SDK auth docs, authenticated MCP servers should implement OAuth 2.1 compatible with the MCP authorization spec, publish protected resource metadata, support dynamic client registration and PKCE, and reject unauthenticated tool calls with `401` plus a `WWW-Authenticate` challenge that points to protected resource metadata.

The server should verify bearer tokens on each MCP request and enforce scopes per tool:

- `study:read` for dashboard, schedule, tasks, grades, and learning spaces.
- `mail:read` for mailbox summaries and message detail.
- `study:write` for enrollment, favorites, waitlists, and other mutating actions.

University credentials must not be placed in ChatGPT widget storage. Apps SDK state guidance separates authoritative business data from message-scoped widget UI state and durable backend state. Widget state is appropriate for selected panels, expanded rows, and view preferences, not for secrets. If ChatGPT needs private university data and the university does not provide OAuth/OIDC delegation, use an explicit account-linking page and store credentials server-side in an encrypted vault keyed by the OAuth subject.

Official docs referenced while writing this design:

- https://developers.openai.com/apps-sdk/build/auth
- https://developers.openai.com/apps-sdk/guides/security-privacy
- https://developers.openai.com/apps-sdk/build/state-management
- https://developers.openai.com/apps-sdk/reference

## Error Handling

- Missing iOS Keychain credentials: show "Save university credentials before loading tasks and deadlines."
- Portal login failure: show the IdP/portal login error when present.
- Portal parse failure: show a concise failure that names the portal and feature.
- Backend missing env credentials: still return service-unavailable errors, but iOS should hit those only for features not yet ported.
- ChatGPT unauthenticated private tools: return `401` with protected resource metadata, not partial data.

## Testing Strategy

- Parser tests first for ILIAS task HTML and Moodle AJAX payloads.
- Facade tests for missing Keychain credentials where injectable credentials are possible without touching the real Keychain.
- Existing iOS unit test suite and build after each slice.
- Backend tests for legacy/dev metadata or docs-only route behavior when code changes.
- ChatGPT TypeScript tests should be added when OAuth middleware is implemented.

## Migration Order

1. Add tested Swift parsers and on-device clients for ILIAS tasks and Moodle deadlines.
2. Switch `AppModel.refreshTasks()` from backend calls to the on-device facade.
3. Mark backend private routes and ChatGPT README as legacy/dev-authenticated.
4. Port grade overview to on-device Alma/Moodle clients.
5. Add ChatGPT OAuth protected-resource metadata, bearer-token verification, and per-tool scope policies.
6. Add optional server-side encrypted credential linking for ChatGPT users if private university data is still needed there.

## Acceptance Criteria For First Slice

- iOS tasks and deadlines refresh no longer calls the backend.
- Missing iOS credentials produce an explicit local error.
- ILIAS task parsing and Moodle deadline normalization have unit coverage.
- The iOS app builds and the test suite passes.
- Backend/ChatGPT documentation no longer implies env-backed private routes are production multi-user auth.
