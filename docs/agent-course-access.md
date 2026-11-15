# Agent course search and request recovery

This describes the repository's observed contracts, not a guaranteed public API.
University systems may change, and network or VPN access may be required. Use
only the student's own authorized account. Do not bypass access controls.

Run `tue-study connectivity` or MCP `campus_connectivity` to check university
service reachability without credentials. On macOS this also reports eduVPN's
connection status, but cannot identify the active institution or prove that
university routes use the tunnel. On other platforms VPN status is unknown.
An HTTP response establishes reachability only, not successful sign-in.
If a service is unreachable, follow the [university VPN instructions](https://uni-tuebingen.de/einrichtungen/zentrum-fuer-datenverarbeitung/dienstleistungen/netze/netzzugang/remote-zugang-vpn/)
and authenticate in the official eduVPN client. The wrapper does not handle
VPN login credentials, connect a tunnel, or disconnect a user's tunnel.

## Independent live course search

```bash
tue-study course-search --query 'Machine Learning' --limit 20
tue-study course-search --query 'Machine Learning' --term '<alma-search-term-value>' --offset 20
```

MCP `study_course_search` exposes the same operation. It queries each service
separately and returns unmerged candidates and a status per source. The agent
compares titles, course numbers, instructors, terms, URLs and descriptions; no
shared identity or current maintenance is assumed. A failed source is an error,
not an empty result. The CLI exits nonzero for a partial failure.

- Alma: authenticated course-offering search. `term` is an Alma **search form
  value**, not a timetable period ID or free-text term label. Omit it to use
  Alma's selected term. The output carries that selected term; a result limit
  can truncate results.
- ILIAS: first search-results page across item types. The wrapper does not filter
  by term here. `has_next_page` refers to the ILIAS results. Use SDK `client.ilias.search(query,
  page=N)` for later pages. Some results may be folders or old courses.
- Moodle: searches the account-visible course catalogue using Moodle's server
  search. `next_offset` is the offset of the next results page; pass `--offset`
  or `moodle_offset` to check it. The offset must be divisible by `limit`.
  Hidden or otherwise inaccessible courses are not guaranteed to appear. The
  wrapper does not apply a term filter to Moodle results.

## Search Alma from a degree programme

Use Alma's module-description filters to search backwards from a degree type
and subject. Fetch the current option labels and values first:

```bash
tue-study alma-program-filters
tue-study alma-program-search --degree 89 --subject 2385 --element-type 5 --limit 50
```

The example values were observed on 15 November 2026 for `Master`,
`Informatik / Computer Science`, and `Veranstaltung` (course). Look up current
values rather than assuming these IDs remain valid. `--degree`, `--subject`,
and `--element-type` can be repeated; different values in a dimension are
searched as separate combinations. `--query` optionally narrows the title or
text. Results include Alma's total and `truncated` flag; the underlying search
caps returned records at 300 and permits at most 24 filter combinations.

The credential-free MCP tools `public_alma_program_filters` and
`public_alma_search_program` provide the same filter values and search. The
Python SDK exposes `client.alma.module_search_filters()` and
`client.alma.search_modules(degrees=(...), subjects=(...), element_types=(...))`.
The existing `course_discovery_search` MCP tool also supports an indexed degree
filter, but index freshness and coverage can differ from the live Alma search.

`Abschluss` is a degree type and `Fach` is a subject; together they do not
identify a specific examination-regulation version or prove a student may count
an individual course. Alma's module-description results are not a guarantee of
offerings in a particular semester. Follow the source links, inspect the module
and programme rules, and check current offerings and registration separately.

## Moodle course contents and explicit links

```bash
tue-study moodle-content --target 12345
```

MCP `study_moodle_content(course_id)` provides the same structured read. It
returns the sections, section descriptions, activity types, names, links and
visible text from the requested course page. Explicit Alma and ILIAS links are
reported with their labels and section/activity provenance. These are evidence,
not automatic course matches; one course can link to multiple records.

Coverage is `visible_course_page`: some course formats, separately loaded
sections, activities, attachments and permissions may prevent a complete view.
The reader does not follow links or submit activities. A missing recognized
course structure is an error rather than an empty course. Links and text may
contain personal data or access tokens; keep output private. If parsing fails,
the raw course-page read below lets an agent inspect the response independently.

## Moodle assignment details and submission form

An assignment activity ID is the numeric `id` in its Moodle `/mod/assign/view.php`
URL, not the course ID. The course-content reader lists activity URLs.

```bash
tue-study moodle-assignment --target 12345
tue-study moodle-submission-inspect --target 12345
```

MCP exposes the same reads as `study_moodle_assignment(assignment_id)` and
`study_moodle_submission_inspect(assignment_id)`. The first returns visible
instructions, source-language submission status fields, feedback fields and
attachment links. Empty feedback does not prove that no feedback exists; Moodle
may not show it yet. Links and text may contain private data.

The second opens the edit-submission form and reports supported file types and
limits when Moodle exposes them. Opening this form may initialize a Moodle draft
file area. It does not upload, save or submit work. Group submissions may affect
other group members. Saving can itself submit for grading, depending on course
settings; upload, save and final confirmation must not be conflated.

## Moodle file submission workflow

The `tue-submit` CLI and opt-in MCP `moodle-write` group support the observed
file-manager form. The flow has only been tested using controlled responses;
uploads and final submission have **not** been verified on the university
server. Do not assume success until the returned receipt confirms the file and
the intended status, and check Moodle if the result is unknown.
Reinstall the package after updating it to add the new `tue-submit` entry point.

```bash
tue-submit review --assignment-id 12345 --file ./work.pdf
tue-submit save --assignment-id 12345 --file ./work.pdf --sha256 <file-hash> --review-sha256 <review-hash> --confirm
tue-submit review-final --assignment-id 12345 --file ./work.pdf
tue-submit submit --assignment-id 12345 --file ./work.pdf --sha256 <file-hash> --confirmation-sha256 <confirmation-hash> --confirm
tue-submit verify --assignment-id 12345 --file ./work.pdf
```

Enable the tools with `tue-mcp --service moodle-write`; they are disabled by
default. They are `moodle_submission_review`, `moodle_submission_save`,
`moodle_submission_review_final`, `moodle_submission_submit`, and
`moodle_submission_verify`. The file path is local to the CLI or MCP server.
Review returns a file SHA-256 and a hash of the reviewed assignment state;
save requires both and an explicit `confirm`. Save uploads one file and sends
the edit form. It may submit immediately or change a group submission.

If the verified result is a draft, review-final shows Moodle's final
confirmation and a hash covering its text, the file, and the assignment state.
Submit requires that hash, the file hash, and `confirm`. If the form has a
submission statement, review and explicitly accept it via `--accept-statement`
or `accept_statement=true`. Unsupported forms fail instead of guessing.

The receipt rereads Moodle and, where an accessible same-host file link exists,
downloads the saved file to compare its bytes with the local file. `submitted`
or `draft` requires both matching bytes and a recognized source status. A
redirect or an upload response alone does not confirm a submission. If a write
times out, or receipt verification returns `unknown`, inspect Moodle before
retrying: the upload or submission may already have happened. No automatic
retry or overwrite is performed. These reads and returned links can contain
sensitive personal information.

## Explicit raw course-page reads

```bash
tue-study raw-course --service moodle --target 12345
tue-study raw-course --service ilias --target 12345
tue-study raw-alma-search --form-only
tue-study raw-alma-search --query 'Machine Learning'
tue-study raw-ilias-search --form-only
tue-study raw-ilias-search --query 'Machine Learning'
tue-study raw-moodle-search --query 'Machine Learning' --page 0 --limit 20
tue-mcp --service raw
```

The opt-in MCP `raw_course_page`, `raw_alma_course_search`, `raw_ilias_search`,
and `raw_moodle_search` tools and CLI calls use locally authenticated sessions and
return decoded response text before result parsing. Course-page reads support
only fixed routes and numeric IDs. Raw Alma search results require the existing
search-form parser; `--form-only` / `form_only` retrieves the form even if that
parser fails. The same distinction applies to raw ILIAS search. Raw ILIAS
returns the first result page only; it does not parse or follow pagination.
Login still depends on existing login parsers. ILIAS and Moodle search redirects
are not followed; a 3xx response is returned as-is and the CLI exits nonzero.
Initial Alma form retrieval follows redirects. After an Alma search POST, the
raw tool follows up to three same-host, same-path redirects that retain the same
flow ID; other redirects produce an error.

**Raw HTML and redirect locations can contain private information and active
session or anti-forgery tokens.** Returning them through MCP can send them to the
agent client or its model provider. Enable this tool only for a trusted local
client; do not place raw output in logs, tickets, commits, or shared prompts.
The tool is excluded from the MCP default services and must be enabled explicitly.

## Observed request contracts

| System and operation | Request flow used by this checkout | Source code |
| --- | --- | --- |
| Alma course search | Authenticated GET to the course-search page; parse the JSF form and its current hidden fields; POST the entered query and optional search-term value to that form's action. | [Client](../package/src/tue_api_wrapper/alma_course_search_client.py), [form parser](../package/src/tue_api_wrapper/alma_course_search_html.py) |
| ILIAS search | Authenticated GET of the search form; POST its current fields and search term; follow explicit search-result pagination for later pages. | [Client](../package/src/tue_api_wrapper/ilias_feature_client.py), [form parser](../package/src/tue_api_wrapper/ilias_feature_html.py) |
| ILIAS course page | GET `https://ovidius.uni-tuebingen.de/goto.php/crs/{numeric-id}`. The normal client follows redirects; the raw tool does not. | [Client](../package/src/tue_api_wrapper/ilias_client.py) |
| Moodle enrolled courses | Authenticate, load `/my/courses.php`, obtain a session key from the page, then call Moodle's AJAX service for `core_course_get_enrolled_courses_by_timeline_classification` with pagination. | [Client](../package/src/tue_api_wrapper/moodle_client.py), [JSON parser](../package/src/tue_api_wrapper/moodle_json.py) |
| Moodle catalogue search | GET `/course/search.php` with `search`, zero-based `page`, and `perpage`. The wrapper checks response shape before reporting results. | [Client](../package/src/tue_api_wrapper/moodle_course_search.py); [Moodle upstream renderer](https://github.com/moodle/moodle/blob/main/public/course/renderer.php) |
| Moodle course page | GET `https://moodle.zdv.uni-tuebingen.de/course/view.php?id={numeric-id}`. | [Moodle client](../package/src/tue_api_wrapper/moodle_client.py) |

Form actions, JSF view state, Moodle session keys, cookies and SAML state are
session-specific. Obtain fresh values from the user's current session. Do not
hard-code values from examples or send credentials to a hosted wrapper. A GET is
not automatically read-only: ILIAS and other portals can expose state-changing
actions as links. Inspect the actual action before issuing arbitrary requests.
Do not automatically retry writes after an uncertain response.

### ILIAS search request sequence

1. The local client signs in through the existing ILIAS and university identity
   provider handoff. The resulting session belongs to the local process.
2. GET `/ilias.php?baseClass=ilSearchControllerGUI`. `--form-only` returns this
   response without parsing its form or submitting a search.
3. For a query, parse the live form action and its current hidden fields. The
   existing parser recognizes an action with `fallbackCmd=performSearch`. The
   raw tool requires HTTPS on `ovidius.uni-tuebingen.de`, path `/ilias.php`,
   `baseClass=ilSearchControllerGUI`, `cmd=post`, and
   `fallbackCmd=performSearch`. It stops if the action differs.
4. Submit the current form fields plus `term` and `cmd[performSearch]` with
   value `Suche`. The normal search implementation also supports optional
   `type`, `filter_type[...]`, and creation-date fields; the raw interface
   uses its default search settings. The response body is returned without the
   search-results parser. HTTP status and `Location` are included.
5. Inspect pagination in the returned HTML. The raw tool does not request later
   pages. The typed `client.ilias.search(query, page=N)` follows pagination
   using the current results parser, so it can also fail when that parser breaks.

The action can contain a rotating `rtoken` query field. Never reuse a captured
value across sessions, persist a live token in documentation, or assume a search
form from one account is valid for another. A successful HTTP response alone
does not establish that it contains authenticated search results. If the form
parser or strict action check fails, inspect the form-only response and the
official interface before changing the implementation.

For deeper investigation see [Alma/ILIAS discovery](alma-ilias-discovery.md),
[Moodle discovery](moodle-discovery.md), and the API's local `/docs` OpenAPI
page. The wrapper's HTTP endpoints are distinct from the upstream portal routes.
