# Student journeys and service scope

Status: working design proposal, 18 November 2026. The scenarios are hypotheses, not findings from student interviews. The [capability inventory](data-and-capabilities.md) describes repository evidence and limits. The [product specification](product-design-spec.md) describes the selected direction.

## Start with a student's question

| Moment | Question | First useful answer | Continue to | Evidence and constraint |
| --- | --- | --- | --- | --- |
| Before leaving | What is next, and has it changed? | Next known meeting, time, place, and any observed cancellation | Meeting detail, schedule, directions | Alma timetable and cancellation client exist. A missing cancellation is not confirmation. |
| Between classes | What must I do and when? | Known dated exercises in order, with course and source | Assignment detail and source action | Moodle and ILIAS reads exist. Coverage and parsed dates can be incomplete. |
| Preparing a class | Where are the materials? | Course workspace with confirmed source links | Material or source course | Multiple systems may describe one course. Never silently infer identity from a similar title. |
| Starting a semester | Which courses can I take? | Search by programme and term, then inspect an offering | Module, course details, registration where supported | Python has programme and offering search. A module is not an offering or proof of eligibility. |
| Handling administration | Where is my enrollment certificate? | Documents entry with available report choices | Select term, obtain official file | Python implements study-service reports; native download needs implementation and live validation. |
| On campus | Where can I eat or study? | Nearby or searchable food and study-space choices, with source freshness | Menu, location or availability | Campus and seat clients exist. Coverage and availability differ by source. |
| Seeking help | Who can help with this question? | Searchable people and advising entry, with contact context | Official contact or service | Directory and advising clients exist; a result is not a confirmed appointment. |
| New to Tübingen | How do I settle in? | Curated routes to university, city, housing and international-student resources | Authoritative external service | These areas include research leads, not verified account integrations. Label external links and check destinations before release. |
| Planning beyond a course | What opportunities are available? | Searchable sports, talks, recordings and career opportunities | Source detail and external action | Dedicated clients exist, with different coverage and access requirements. |

## Information architecture: proposed, not fixed

The four destinations in the product specification are a testable starting point. They are not a requirement to retain any current navigation. Their purpose is to make recurring tasks visible and make infrequent tasks findable.

- **Today:** next commitment, known changes and deadlines. Documents have a direct entry, because the user named them as a primary task.
- **Schedule:** dated commitments and work. A cancellation stays visible with its source; undated work has a separate list.
- **Courses:** current courses, their confirmed source connections, work and materials. Include programme-based course discovery and make enrollment, LMS membership and exam registration distinct.
- **Campus:** search plus clear intent groups: food and study places; people and support; student life and opportunities; settling in. Each group opens a focused list and detail, rather than another flat feature menu.
- **Account:** accessible from every destination; documents, academic records, connections, privacy and settings. Search must also find documents and services.

Global search should search only sources the app has actually indexed or queried. Show the scope and source of results. A service directory can link to an official page when no integration is available; it must not present a link as an account connection.

## Scope decisions

These are prioritization proposals for design and validation. They do not authorize deleting working capabilities.

| Treatment | Capabilities | Reason |
| --- | --- | --- |
| **First-class** | Timetable, observed cancellations, dated exercises, course context, documents | Directly support the chosen attention-first outcome and the user's named needs. |
| **Findable, not on Today by default** | Grades and exams, course and programme discovery, mail, notifications, food, spaces, people, sport, talks, recordings, careers | Valuable in particular moments; placing all of them on the home screen competes with the next action. Preserve access and source identity. |
| **External or future investigation** | Housing, city administration, international support and library account where no verified integration exists | Student needs extend beyond the implemented clients. Begin with verified official destinations; do not promise account data. |
| **Defer or disable by default** | Automatic cross-portal course merging, inferred mail priority, automatic background actions, broad unsolicited notifications | Their correctness and usefulness are not established. Explicit matching and opt-in reminders are safer to test. |
| **Do not remove on design evidence alone** | Less frequent services and write operations | Measure use and understand student consequences before any separate removal decision. |

## Detailed interaction rules

### Attention feed

An item has a source identifier, source-specific timestamp, optional event or due date, and a link to its original detail. Keep deadlines, meetings and changes semantically distinct. Order known deadlines chronologically within their group; do not invent a deadline for an undated item. Show a cancellation only when the source reports it, and retain the original time and course. If a refresh fails, identify the affected source and show the last successful check. Never infer “nothing due” from an incomplete scan.

### Course identity

An Alma offering, ILIAS course and Moodle course are separate records. Link only with a reliable identifier or source link, or after a student explicitly confirms a proposed match. Explain why a proposed match was suggested. Keep unmatched records visible, and allow confirmed matches to be inspected and undone. A match does not assert registration or exam eligibility.

### Connections and onboarding

Let a student explore public information first, or connect their university account. Explain what each service supplies before connection. Saving credentials and successfully authenticating are separate states; report failures per service. Keep credentials and private requests local to the device. Ask for notification permission only in the context of a chosen reminder, and explain Lock Screen visibility before enabling private details.

### Service action

Show the exact target, current source state and consequence before a registration or submission. Require an explicit confirmation for the final write. Report the source response. If the result is unknown, guide the student to inspect the source before retrying. Never label a draft as submitted.

## Research and validation plan

1. Interview students across faculties, degree stages, language needs and commuting patterns. Ask them to reconstruct a recent day and an administrative task, rather than asking whether they like a feature list.
2. Test the proposed navigation with five tasks: find a cancellation, find a deadline, obtain an enrollment certificate, discover a programme offering, and find student support. Record the first route taken and where the participant expects the answer.
3. Test the concept with a disconnected account, one failed source, no known deadlines, an unmatched course and a stale timetable. Ask what the student believes is missing and what they would do next.
4. Validate source coverage with consent and representative accounts. Record the source, term, scan limit, check time and failure; do not export private data into research artifacts.
5. Establish performance baselines on representative devices before optimization: launch to usable content, network requests, scrolling and memory. Compare the same scenario after a change.

Success is a student finding and understanding the requested item, including its source and limitations. Time and navigation errors help diagnose the design; small qualitative sessions cannot establish population-wide success.

## Open decisions before delivery

- Validate whether documents deserve a permanent primary destination or a direct Today shortcut plus search.
- Determine which deadline sources and cancellation signals are sufficiently complete for alerts.
- Decide course matching evidence and correction flow after inspecting real, consented records across faculties.
- Validate native document retrieval and the official fallback route for unsupported reports.
- Review the existing uncommitted implementation against the approved design. Keep, revise or discard individual changes only after that review.
