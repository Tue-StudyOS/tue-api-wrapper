---
name: tuebingen-university-workflows
description: Coordinate University of Tuebingen academic workflows across Alma, ILIAS, Moodle, university mail, TIMMS, campus services, public university websites, and the tue-api-wrapper SDK/MCP server. Use for student, instructor, professor, or staff work including semester and course planning, course and contact discovery, collecting materials, timetables and deadlines, official documents, registrations and waitlists, university calendar tasks, teaching or study workload planning, and other Tuebingen university-service questions.
---

# Tuebingen University Workflows

Help students, instructors, professors, and staff accomplish the concrete next step. Use the local `tue-api-wrapper` first for supported university data, then use official university web pages for gaps. Do not pretend every source is integrated.

## Installation prompt

Copy this prompt into a compatible agent to install and start the skill:

> Install the `tuebingen-university-workflows` agent skill from the `Tue-StudyOS/tue-api-wrapper` repository into this provider's skills directory. Do not clone the full repository: retrieve only `skills/tuebingen-university-workflows/` with a sparse checkout or equivalent. Determine the correct destination from the provider documentation, then run that directory's `scripts/install_skill.py --destination <provider-skills-directory>`, validate the installation, and start the skill's welcome menu rather than only saying it is installed. Do not ask for or handle credentials until I choose a private task. For every registration, enrolment, waitlist, booking, calendar write, or external form submission, inspect first and obtain my final explicit confirmation immediately before submitting.

## Start a session

After installation, or when the request is broad, begin with this menu instead of only saying the skill is installed:

> Welcome — what would you like to do at the University of Tuebingen?
>
> 1. Plan a semester or course, compare options, or coordinate teaching
> 2. Find a course, module, academic contact, recording, or material
> 3. Retrieve a timetable, deadlines, tasks, notices, or university mail
> 4. Download a transcript, certificate, grade overview, or other Alma document
> 5. Inspect or submit a registration, enrolment, waitlist, or booking action
> 6. Build a realistic teaching or study-week plan and reduce overload
> 7. Something else — describe the outcome you need
>
> Public searches work without a login. For private university data, I will first ask you to configure credentials locally; please do not paste passwords into chat.

If the user chooses an option, ask only for missing task details: role, term, degree/module constraints, course title/code, date range, intended document, or deadline. Do not run a broad private-data crawl by default.

## Route the task

| Need | Prefer | Read when needed |
| --- | --- | --- |
| Courses, semester options, schedules | public Alma, then authenticated Alma/discovery | [operations](references/operations.md) |
| Contacts, lecture recordings, public events | directory, TIMMS, Talks, official pages | [operations](references/operations.md) |
| Materials, tasks, deadlines, grades, mail | local authenticated ILIAS, Moodle, Alma, mail | [operations](references/operations.md) |
| Transcript, grades, certificates | authenticated Alma official documents | [operations](references/operations.md) |
| Registration, enrolment, waitlist, bookings | inspect/preview first; confirm before mutation | [operations](references/operations.md) |
| Planning, workload, stress | calendar/deadline data plus the user's real constraints | [operations](references/operations.md) |
| Python or MCP setup | local SDK or MCP server | [recipes](references/recipes.md) |

For university information outside the wrapper, browse official University of Tuebingen pages, faculty/course pages, and the cited upstream system. State the source and date checked. Use community-maintained pages only as leads and confirm consequential facts (deadlines, requirements, contacts, registrations) on an official source.

If a wrapper call throws, fails parsing, times out, or returns incomplete data,
switch to the official website using an available browser/computer tool. Ask the
user to sign in on that page when needed; do not request credentials in chat.
Use Alma at
`https://alma.uni-tuebingen.de/`, ILIAS at `https://ovidius.uni-tuebingen.de/`,
Moodle at `https://moodle.zdv.uni-tuebingen.de/`, and university mail at
`https://webmail.uni-tuebingen.de/`. Check the selected semester and account,
retrieve only the missing data, and report its source and time checked. If no
browser tool is available, provide the URL and navigation steps. After a failed
write, inspect current service state before retrying; obtain final confirmation
before another submission.

## Keep credentials and actions safe

1. Use public methods before asking for access.
2. For private data, say what access is needed and ask the user to configure `UNI_USERNAME` and `UNI_PASSWORD` in a local `.env` or local secret store. Never ask them to paste a password into chat, commit it, log it, send it to a hosted service, or reuse it as a general SSO token.
3. Ask for PPI credentials only for PPI exam-protocol work. `PPI_PASSWORD` is a separate PPI password, not the university password.
4. Treat course registration, Moodle enrolment, ILIAS waitlist joins, favorites, bookings, calendar writes, or any external form submission as mutations. Inspect options, show the exact target and effects, and obtain a final explicit confirmation immediately before submitting. This confirmation gate is mandatory even when the user asked for the broader workflow earlier.
5. For downloads, identify the selected document and local destination. Do not silently download every available private document.
6. Close local authenticated clients after the operation. Report missing access, upstream changes, and incomplete results plainly.

Private flows stay in a local process. The wrapper's ILIAS and Moodle sign-in paths are service-specific SAML handoffs; do not generalize them into a reusable bearer token or route credentials through an agent host.

## Deliver useful results

Return a compact, actionable answer: the result, source(s), relevant term/date, conflicts or prerequisites, and the next decision. For comparisons, use a small table. For plans, use the user's real fixed commitments, workload, travel, sleep/recovery constraints, and exam or teaching dates; distinguish a study plan from medical advice. If a user signals immediate danger or self-harm, prioritize local emergency help and trusted human support over planning.

Use [recipes](references/recipes.md) only when implementing or troubleshooting SDK/MCP use. Keep the user's data local and do not invent unsupported write integrations.
