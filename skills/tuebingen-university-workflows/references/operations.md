# University workflow operations

## Source selection

Start with the smallest source that can answer the question.

| Task | Source and method | Notes |
| --- | --- | --- |
| Compare modules/courses | Public Alma `search_modules`, then `module_detail` | No login; verify current term and capacity separately. |
| Find official contact | Public directory `search`, then faculty/course page | Match role and department, not just name. |
| Find recordings/material leads | TIMMS `suggest`/`search`; ILIAS `search`/`content`; Moodle course detail | Cite the actual course/item URL; request selection before bulk downloading. |
| Semester planning | Alma timetable/course offerings, course discovery, degree rules on official pages | Separate confirmed timetable conflicts from unverified preferences. |
| Personal timetable/tasks | Alma `timetable_view`/`timetable_course_assignments`; ILIAS `tasks`/`assignment_deadlines`; Moodle `deadlines` | Ask for term/date window and return conflicts and dates in Europe/Berlin. |
| Calendar management | Aggregate the timetable, deadlines, and public events; create an importable plan or use an available calendar connector | Ask before creating, changing, or importing calendar entries. |
| Private documents | Alma `exam_reports`, `download_exam_report`, `studyservice_documents`, `download_document` | Ask which document and local destination before download. |
| Course action | Alma registration support/options; Moodle course/enrolment; ILIAS waitlist support | Preview and obtain final confirmation before `register_for_course`, `enrol_in_course`, or `join_waitlist`. |
| Mail and portal notices | Mailbox summaries/message detail; Alma portal messages | Minimize scope: inbox summary or specific search first. |
| Campus day-to-day | Campus events/canteens/seats/buildings; Anny resources/calendar | Treat any booking/appointment as a mutation. |

## Private access

Explain the boundary before private reads:

> To retrieve your private university data, the wrapper needs a local university session. Please configure `UNI_USERNAME` and `UNI_PASSWORD` in a local `.env` or secret store on this machine. Do not send the password here. Tell me when it is configured and which systems you want to access (for example, Alma and ILIAS only).

Use the minimum requested systems. `UNI_USERNAME`/`UNI_PASSWORD` are for the local authenticated wrapper. They are not credentials an agent should forward to a remote API. PPI is separate and only uses `PPI_USERNAME`/`PPI_PASSWORD` for PPI work.

## Planning and aggregation

For a semester plan, collect in this order:

1. Degree/program, term, target credit load, required/elective modules, and fixed constraints.
2. Candidate courses from Alma plus official module rules; add private offerings only with the account owner's consent.
3. Meeting times, registration deadlines, prerequisites, assessment formats, and material availability.
4. Conflicts and feasible alternatives. Label unknown availability or registration status.
5. A decision-ready short list and next action for every remaining uncertainty.

For a teaching or study-week plan, first gather deadlines/exams and the user's recurring obligations. Allocate focused blocks, review/catch-up time, and recovery. Do not diagnose stress or promise health outcomes; encourage a student to use university counselling or health support when overwhelm is persistent or severe.

## Confirmation pattern for actions

Before a mutation, show a brief preview:

> I found the registration path for **[course]** in **[term]**. Submitting will register/join the waitlist using your current local university session. Shall I submit this exact action now?

Only execute after an unambiguous yes to that exact action. If the site presents an agreement, consent page, or multiple registration paths, show them and request a choice. Report the upstream result, not an assumption of success.

## Web fallback

Use the web for an unsupported source, official degree regulation, faculty contact, current deadline, or a university page the wrapper does not expose. Do not scrape behind a login as a replacement for a supported local client. When a public page changes or conflicts with wrapper data, prefer the current official page and say what differs.
