# TIMMS Discovery

Discovery date: 2026-04-06

This note summarizes new student-facing surfaces discovered from:

- `timms.uni-tuebingen.de.har`
- a public follow-up check against `timms.uni-tuebingen.de`
- adjacent services linked from the same session: `www.praxisportal.uni-tuebingen.de` and `epv-welt.uni-tuebingen.de`

No credentials, cookies, bearer tokens, or full private captures are stored here. Query parameters and auth fields are described by name only.

## Existing Gap

This note predates the current TIMMS and Praxisportal clients. Check the SDK for implemented coverage.

## TIMMS Contracts

Observed or verified public routes:

| Route or flow | Observed contract | Inferred capability | Student value |
| --- | --- | --- | --- |
| `/List/Browse` | HTML content tree with faculty and institute nodes | browse media by faculty, institute, lecture, and collection | `very high` |
| `/List/OpenNode?nodepath=...&nodeid=...` | id plus human-readable path segments | lazy tree expansion and scoped media browsing | `very high` |
| `/List/CloseNode?nodepath=...&nodeid=...` | same query shape as open | collapse tree state or preserve path-aware navigation | `medium` |
| `/Search/Find` | search entry page; links to author and date index | discovery landing page for media search | `high` |
| `/Search/_QueryControl?InputQueryString=...` | GET search endpoint | full-text search returning item hits and timecode deep links | `very high` |
| `/Search/AutoCompleteSearch?term=...` | JSON array of `{ value }` suggestions | autocomplete while typing in search UIs | `high` |
| `/List/AuthorIndex` | public author index with video and audio counts | browse media by lecturer or contributor | `high` |
| `/List/Author?lastname=...&firstname=...` | author detail page linked from author index | fetch all media for a person | `high` |
| `/List/DateIndex` | public chronological entrypoint | browse archived material by creation date | `medium` |
| `/tp/{id}` | stable media detail page | title, creator, subjects, creation date, identifier, rights, related items | `very high` |
| `/Player/EPlayer?id=...&t=...` | iframe-backed player route | media playback with time offset support | `very high` |
| `/api/Cite?id=...&format=bibtex|enw` | plain-text citation export | bibliographic export for recorded lectures or talks | `medium` |

Notable details:

- Search results include `starttime` deep links on `/tp/{id}`, which means TIMMS already exposes chapter-like time jumps without extra scraping.
- The item page iframe loads `/Player/EPlayer?id=...&t=...`.
- The player HTML contains a base64-encoded source list with direct MP4 variants, including width, height, bitrate, and resolved file URL.
- The tested item page exposed two MP4 variants for the same lecture, which suggests a quality-selector contract is feasible.
- Item pages also expose Dublin Core-like metadata fields such as creator, subjects, description, publisher, creation date, local type, identifier, language, and rights URL.

## TIMMS Features To Add First

### 1. Media search with timecode jumps

Why it matters:

- TIMMS already holds a large archive of lecture recordings and talks.
- Search results are more useful than plain title matches because they can jump to specific timestamps.
- This is the highest-leverage way to turn TIMMS into a study tool rather than a passive portal.

Suggested wrapper surface:

- `GET /api/timms/search?query=...`
- `GET /api/timms/search/suggest?term=...`

### 2. Media detail and stream variants

Why it matters:

- `/tp/{id}` pages expose stable identifiers and rich metadata.
- The player iframe exposes concrete MP4 variants instead of only opaque browser playback.
- This supports watch later, copy stream URL, transcript-like indexing later, and richer embedding in the app.

Suggested wrapper surface:

- `GET /api/timms/items/{id}`
- `GET /api/timms/items/{id}/streams`
- `GET /api/timms/items/{id}/cite?format=bibtex|enw`

### 3. Faculty and course archive browser

Why it matters:

- `/List/Browse` plus `/List/OpenNode` gives a browsable tree of faculties, institutes, and lecture series.
- The capture showed deep paths down to Informatik and single-lecture items.
- This matches how students often remember material: by course or lecturer, not by keyword.

Suggested wrapper surface:

- `GET /api/timms/tree`
- `GET /api/timms/tree/node?nodeId=...&nodePath=...`

### 4. Lecturer-centric discovery

Why it matters:

- `/List/AuthorIndex` exposes public creator pages with media counts.
- This enables a "show me everything by this lecturer" workflow.
- It also pairs well with existing Alma and ILIAS course detail screens.

Suggested wrapper surface:

- `GET /api/timms/authors`
- `GET /api/timms/authors/{lastname}/{firstname}`

## Praxisportal Contracts

The TIMMS session also traversed the public university Praxisportal after Shibboleth login.

Observed routes:

| Route or flow | Observed contract | Inferred capability | Student value |
| --- | --- | --- | --- |
| `/candidate/search` | authenticated candidate search page | internship and job discovery | `very high` |
| `/1/projecttype/list` | JSON route | project type filters | `high` |
| `/1/industries` | JSON route | industry filters | `high` |
| `/1/experiences` | JSON route | experience-level filters | `high` |
| `/1/project/increment_search_view` | POST with `project_ids` JSON array | lazy detail loading for search hits | `high` |
| `/1/project/{id}` | JSON route | full project detail | `very high` |
| `/1/subscription/types` | JSON route | available alert types | `medium` |
| `/1/subscription/create` | POST with query payload plus subscription type | saved search alerts | `high` |
| `/1/faculty` and `/1/faculty/{id}` | authenticated JSON routes | faculty and institute selection | `medium` |
| `/1/user/set_institute` | POST with `faculty_id`, `institute_id`, `token`, `access_token` | onboarding to a faculty context | `medium` |
| Algolia `POST /1/indexes/projects_prd/query` | third-party search backend used by the portal | search bootstrap and ranking source | `medium` |

Recommended product framing:

- keep it student-focused: jobs, internships, filters, and saved alerts
- do not start with profile editing or onboarding mutations

Suggested wrapper surface:

- `GET /api/praxisportal/projects`
- `GET /api/praxisportal/projects/{id}`
- `GET /api/praxisportal/filter-options`
- `POST /api/praxisportal/subscriptions`

## EPV Contracts

Observed routes:

| Route or flow | Observed contract | Inferred capability | Student value |
| --- | --- | --- | --- |
| `GET /RestrictedPages/StartSearch.aspx` | public people-search form page | person lookup entrypoint | `medium` |
| `POST /RestrictedPages/StartSearch.aspx` | ASP.NET postback with one visible search field for name | name-based people search | `medium` |
| `GET/POST /RestrictedPages/SizeLimitExceeded.aspx` | overflow flow after broad matches | search refinement path | `low` |
| `GET /RestrictedPages/EmptyResult.aspx` | no-hit result page | explicit empty-state handling | `low` |

Observed form field:

- `ctl00$MainContent$SearchControl$NameTextBox`

This looks useful for a lightweight people lookup, but it ranks below TIMMS and Praxisportal because it is narrower and the form is classic ASP.NET postback rather than a clean JSON surface.

## Recommended Build Order

1. TIMMS search and autocomplete.
2. TIMMS item detail plus stream-variant extraction.
3. TIMMS faculty or course tree browsing.
4. Praxisportal project search and project detail.
5. Praxisportal saved search alerts.
6. EPV people lookup.

## Product Interpretation

The combined pattern is strong:

- TIMMS is the best new archival learning surface.
- Praxisportal is the best new career-facing surface.
- EPV is useful, but it is more supporting infrastructure than a headline feature.

That points to two high-value product additions:

- a `study archive` area for lecture recordings, cited talks, and timecoded search
- a `career` area for internships, jobs, and saved alerts

## Confidence Notes

- High confidence:
  - TIMMS tree browsing
  - TIMMS search, autocomplete, item detail, citation export, and player-backed MP4 variants
  - Praxisportal project search, project detail, filters, and subscriptions
- Medium confidence:
  - TIMMS date-index drilldown beyond the public entry page
  - Praxisportal faculty onboarding semantics
  - EPV result-page parsing beyond the name-search postback
