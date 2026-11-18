# Local MCP Server

The package includes a local MCP server so agents can call University of Tübingen tools without every project writing its own server.

## Install

```bash
cd package
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[mcp]"
```

## Credentials

Public tools do not need credentials.

Authenticated tools read credentials from environment variables or a local `.env` file:

```bash
UNI_USERNAME=your-zdv-id
UNI_PASSWORD=your-password
```

The same university username and password are used for Alma, ILIAS, Moodle, and mail.

## Run With Stdio

Most local MCP clients use stdio:

```bash
tue mcp
```

Example MCP client command:

```json
{
  "mcpServers": {
    "tue-api-wrapper": {
      "command": "tue",
      "args": ["mcp"]
    }
  }
}
```

If the command is not on your PATH, use the full path as `command`, for example `package/.venv/bin/tue`, and retain `"args": ["mcp"]`.

## Run With HTTP

For HTTP-based tools:

```bash
tue mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

The MCP endpoint is:

```text
http://127.0.0.1:8765/mcp
```

## Tool Groups

For independent course search, opt-in raw course responses, and observed portal
request contracts, see [Agent course access](agent-course-access.md).

The `study` group adds read-only study tools. Enable only this group with
`tue mcp --service study`; omit `--service` to enable all groups except `raw`. The server
also retains the existing service groups listed below.

- `study_radar_read` reads the upcoming Alma timetable, bounded ILIAS assignments
  and quizzes, Moodle deadlines, and Alma notices, with a status for each source.
- `study_radar_changes` compares those sources with a local snapshot and updates
  it. The first successful check of each source establishes its baseline.
- `study_timetable`, `study_alma_exams`, `study_alma_enrollments`, `study_alma_notices`,
  `study_ilias_memberships`, `study_ilias_content`,
  `study_ilias_assignment_deadlines`, `study_moodle_courses`, `study_moodle_content`,
  `study_moodle_assignment`, `study_moodle_submission_inspect`,
  `study_moodle_notifications`, `study_moodle_grades`, and
  `study_mail_message` expose existing read-only data.

The public tools `public_alma_program_filters` and `public_alma_search_program`
search Alma by degree type, subject and record type. See the [programme search
guide](agent-course-access.md#search-alma-from-a-degree-programme) for limits
and how to interpret the results.

The credential-free `campus` group provides `campus_buildings`,
`campus_people_search`, `campus_rooms_search` and `campus_fitness_courses`.
Combine service selections with repeated `--service` flags.

The `registration` group provides `alma_registration_inspect` and
`alma_registration_prepare` for Alma course and exam registration. Preparation
opens Alma's registration workflow to retrieve options; it does not send the
final registration. Exam preparation stops if Alma requires acceptance of an
instruction screen. The MCP server does not expose a final submission tool:
MCP elicitation can be answered by an agent and cannot enforce the required
independent user review. Use the interactive CLI described below.

## Alma registration CLI

After installing the package, find the course or exam detail URL in Alma and run:

```bash
tue register inspect course --url 'https://alma.uni-tuebingen.de/alma/...'
tue register options course --url 'https://alma.uni-tuebingen.de/alma/...'
tue register prepare course --url 'https://alma.uni-tuebingen.de/alma/...' --option '<planelement-id>'
tue register execute course --url 'https://alma.uni-tuebingen.de/alma/...' --option '<planelement-id>'
```

Replace `course` with `exam` for an exam. Provide `--exam-id` when needed to
select a linked exam. The execute command reads fresh options, displays the
account, target and selected path, and asks the user to type `REGISTER` in an
interactive terminal. It checks the target and path again before submitting.
It does not execute from a noninteractive input. If Alma requires an instruction
screen to be accepted, this interface stops; review that flow in Alma.

After an attempted submission, inspect the result in Alma. The existing parsers
do not establish that a selected registration was accepted, so this interface
reports `unverified` and exits nonzero even if Alma returned a response. A
connection error reports `unknown`: inspect Alma before any retry, because the
request may have reached the server. No live registration was performed while
developing this interface.

The radar reports additions and changes only. An item missing from a later
check is not considered removed or completed. ILIAS scans only directly listed
exercises and quizzes, with course and item limits. Moodle uses a moving
look-ahead window. ILIAS dates may be relative display strings, and Alma items
are notices, not necessarily deadlines. Inspect source status before concluding
that no items exist.

Timetable identity uses the source event UID and the occurrence's Berlin date.
A time or room change on the same date can be reported as changed. A move to a
different date appears as an addition; the old occurrence is not reported as
removed. When UIDs are absent or multiple occurrences share a UID and date,
`identity_warning` is true and change matching is less reliable. Check
`truncated`, `term`, and the reported timetable window. This is not a complete
calendar cancellation detector. The default term is the current university
term; pass `--term` or the MCP `term` parameter for another term.
The radar reads one term per check, so a window spanning a semester boundary
does not automatically include the next term.

Snapshots contain private course information. They are stored per account under
`${XDG_DATA_HOME:-~/.local/share}/tue-api-wrapper/study-radar/` with private file
permissions. Delete the account's snapshot to reset its baseline. Do not share
the directory. Avoid concurrent snapshot updates: they are not synchronized.

The `moodle-write` group is opt-in and exposes reviewed file save and final
submission actions. See [Moodle file submission workflow](agent-course-access.md#moodle-file-submission-workflow)
for confirmation, group-submission, receipt, and current verification limits.

The `forum-write` and `quiz-write` groups are also opt-in. Read their
[forum and quiz guide](forum-and-quiz-access.md) before enabling writes; live
post and quiz-attempt writes have not been verified during development.

## JSON CLI

After installing the package, use:

```bash
tue study --days 30 --limit 50
tue study --days 30 --limit 50 --changes
tue study timetable --term "Winter 2026/27" --days 7
tue study exams
tue study content --target crs/12345
tue study moodle-courses --limit 20 --offset 0
tue study moodle-content --target 12345
tue study moodle-assignment --target 12345
tue study moodle-submission-inspect --target 12345
tue study mail-message --target 123 --mailbox INBOX
tue study buildings
tue study rooms --query "Gruppenraum"
```

The first command reads current observations without saving a snapshot. The
second compares and updates the same account-specific snapshot used by MCP.
Both write JSON to stdout and return exit status 1 when any source fails.
`--days` applies to Moodle and the timetable; ILIAS date strings are returned
as displayed. `tue study --help` lists all available resources. The public
`buildings`, `canteens`, `seats`, `people`, and `rooms` commands need no login.

Public tools:

- `public_alma_search_modules`
- `public_alma_current_lectures`
- `public_campus_events`
- `public_campus_canteens`
- `public_timms_search`

Authenticated tools:

- `authenticated_alma_timetable`
- `authenticated_ilias_tasks`
- `authenticated_moodle_deadlines`
- `authenticated_mail_inbox`

## Design Notes

This MCP server is intended for local student projects and agent experiments. It keeps university credentials in the local process and does not provide multi-user hosted authentication. Do not expose authenticated tools to an untrusted host.
