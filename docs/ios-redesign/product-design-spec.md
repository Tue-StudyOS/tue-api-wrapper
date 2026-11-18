# A student companion for Tübingen

Status: design proposal for discussion, 18 November 2026. This is a fresh product direction, not a description of the current UI. The [capability inventory](data-and-capabilities.md) separates existing code from work still needed. Screen examples use fictional data.

The [student journeys and scope](student-journeys-and-scope.md) maps needs to sources, proposed placement and validation work.

## Product intent

Help Tübingen students understand what needs attention today, then reach the course, document or service behind it. The app should make scattered systems understandable without pretending that all data has been found, matched or refreshed.

**Audience:** students across degrees and faculties, including international students. Start with personal university data, then make public campus information accessible without an account.

**Design principles**

1. Lead with a decision: what is next, what changed, and what is due.
2. Organize around a student's task or course, not around a portal's name.
3. Preserve source, freshness and uncertainty. Separate “no items found” from “could not check.”
4. Keep account access and sensitive data on the device. Ask before showing private content on a Lock Screen.
5. Use native navigation, accessible text sizes, clear labels and useful offline states.
6. Be quiet and precise: generous space, strong type, limited color, no decorative status indicators.

## Directions considered

| Direction | Strength | Trade-off |
| --- | --- | --- |
| **Student companion — selected** | Starts with attention and connects each item to its course. | Requires careful source attribution and linking logic. |
| Planner first | Excellent for time-blocking and calendar-heavy work. | Makes documents, course context and administrative notices feel secondary. |
| University hub | Easy to locate an individual service. | Pushes the student to know which service holds the answer. |

## Proposed information architecture

Four destinations are a design proposal, not a commitment to keep any current screen.

- **Today:** next commitment, changes and due work; a clear route into each item.
- **Schedule:** day/week view of lectures, exams and deadlines when their dates are known. Cancellations remain visible and labeled.
- **Courses:** active courses as the durable organizing object. A course collects confirmed links to timetable, assignments and available material. It must show unmatched records rather than silently merging them.
- **Campus:** food, places, study spaces, sports, people, talks and opportunities, grouped by student intent and searchable. Less frequent features live here instead of becoming tabs.

A profile/control entry gives access to documents, academic records, university account connections, notifications, widgets, privacy and service status. Documents are also reachable from search and relevant enrollment context. A search entry finds courses and services without requiring the student to know their source system.

## Core student flows

### 1. Open the app and understand today

1. Show a short date header and the next scheduled commitment with time and place.
2. Show actionable changes, such as a cancelled class, with source and last successful check.
3. Show due work in a single chronological list when dates are reliably parsed. Undated items remain separate; never guess their order.
4. Opening an item shows its details and available action. The source and any incomplete checks remain visible.
5. If a source fails, show which data could not be checked and the last successful update. Do not say “all caught up.”

The feed is a prioritization model, not a claim that the app knows what matters most. Initial ordering is deterministic: active urgent changes, upcoming deadlines, next commitments, then lower-urgency notices. Avoid assigning importance to mail without a verified rule and user control.

### 2. Work in a course

A course page has a clear title and term, next meeting, upcoming work, materials and relevant messages. Each section identifies its source and incomplete loading. Link course records only when an explicit identifier, source link or student-confirmed match supports it. A student can inspect and undo a match. A course missing an ILIAS or Moodle match remains usable.

### 3. Find an official document

A student chooses a document type and, where needed, a term. Show the official source and exact selected document before download. Fetch privately on device and offer the native share/save interface after verifying the returned file. If a report needs a new form or an unsupported step, explain the limitation and offer the official Alma page. Native retrieval is not implemented by this design.

### 4. Explore without an account

Offer a visible route into public campus information before sign-in. Explain that private timetable, work and documents need a university account. Connect services in context and explain what data each connection retrieves. Saving credentials is not proof of a successful login; show actual connection state after a real request.

### 5. Act on a submission or registration

Show the exact course, file or registration target, current source state and consequences. The student explicitly confirms an action before the app sends it. Show the returned state and source. If the response is uncertain, inspect the service before offering retry. Do not equate a saved draft with a final submission.

## Native surfaces

| Surface | Proposal | Trust and interaction |
| --- | --- | --- |
| Home Screen widget | Next lecture and one following commitment; optional due-work variant later. | Cached content with last update and an open-app action. No claim of continuous refresh. |
| KuF Pass widget | Home Screen and Lock Screen shortcut to the saved KuF pass. | Opens the pass in the app. The shortcut carries only the destination. |
| Lock Screen widget | Next lecture time with a privacy-conscious, user-selected level of detail. | Default to minimal content; no grades or document names. Respect WidgetKit timing. |
| Live Activity | Explicitly start a relevant lecture activity, with time and room when available. | Do not imply background auto-start or guaranteed updates. Dismiss or end according to observed state and system rules. |
| Notifications | Optional lecture and due-work reminders, plus cancellation alerts only when a reliable change is observed. | Separate permission from preference. Avoid duplicate alerts and never assert a cancellation based on a failed fetch. |
| Shortcuts / Spotlight | Explore later for opening a chosen course, today, or documents. | Feasibility and privacy review precede any promise. |

## Design sheet

**Character:** calm, confident, information-led; native iOS rather than a miniature website. The visual reference is the restraint and hierarchy of Stageshow product imagery, adapted to real accessible controls and real data.

**Color:** system background and foreground adapt to light/dark mode. A single university-red accent marks interactive emphasis; cancellation and warning use explicit text and symbols, not color alone. Meet contrast requirements in both modes.

**Typography:** system type with Dynamic Type. One clear page title, compact secondary metadata, readable event titles. Avoid all-caps labels as the main hierarchy.

**Layout:** one primary focal item, followed by grouped lists. Prefer separators and native list patterns to a stack of equally weighted cards. Use a card only when it groups a decision or distinct surface.

**Components:** native tab/navigation bars, system buttons, sheets, search, share and accessibility actions. Build reusable event row, work row, source/status line and empty/error states; preserve stable identity.

**Motion:** short, meaningful transitions. Respect Reduce Motion. Never animate to imply freshness or completion.

**Accessibility:** test VoiceOver order and labels, large Dynamic Type, contrast, reduced transparency, reduced motion and small screens. Controls must keep usable touch targets and wrap rather than truncate necessary information.

**Visual examples:** [overview concepts](concept-screens.html) and [interactive flow mockups](flow-mockups.html). The mockups use fictional records and include alternate outcomes for sign-in, data refresh, documents and submissions.

## Screen and state specification

| Screen | Primary task | Required states |
| --- | --- | --- |
| Welcome / connect | Understand benefit, explore publicly or connect university account | No account, local save error, sign-in pending, successful or failed service connection; never imply credentials were verified on save alone. |
| Today | Decide what needs attention | Loading, no data, partial source failure, last-known data, cancellations, due and undated items, genuinely empty after successful checks. |
| Schedule | Find time/place and notice changes | Day/week, current/other term, cancelled, no events, failed or stale source. |
| Course | Understand a course and act on work | Confirmed/missing links across sources, partial service failure, current vs past term, unavailable activity. |
| Item detail | Inspect before opening, submitting or registering | Read-only, review, in progress, confirmed, failed, unknown; preserve source result. |
| Documents | Choose and obtain an official file | Login needed, available choices, term required, generating/downloading, verified file, unsupported/error. |
| Campus and search | Find a service or answer | Public access, search results, no results, stale/unavailable source, external link. |
| Account and privacy | Manage connections, data and system surfaces | Connected/failed/disconnected per service; remove local credentials and cached private data, controls for widget privacy and notifications. |

## Acceptance checks for a future implementation

- A student can find the next lecture, any known cancellation and the next known deadline without selecting a portal.
- A failed Moodle or ILIAS check is visible even when other data loads; an empty feed never implies complete coverage.
- A student can reach an official document flow without guessing where it lives; native download is only labeled available once validated.
- A course match is explainable and reversible; enrollment, LMS membership and exam registration remain separate facts.
- Public exploration works without credentials. Private requests use on-device credentials; secrets never enter hosted services or logs.
- Each write has an explicit target, confirmation and source-backed outcome; unknown outcomes do not trigger automatic retries.
- Native widgets are tested for stale cache, cancellation, no-data and privacy states. Refresh timing is described as system controlled.
- Test VoiceOver, large text, both appearances, small screens and offline/partial-service states on simulator and a physical device.
- Measure startup, main-thread work, memory and scrolling before and after; do not claim an optimization from code inspection alone.

## Decisions and open work

- User chose the student companion direction and attention-first home. Specific navigation labels and hierarchy above remain proposals.
- Verify with students across faculties which dates, changes and documents they need most; do not treat one account as representative.
- Resolve document handling, course matching, source freshness and reliable cancellation changes before committing a delivery scope.
- Audit Swift 6 language-mode diagnostics separately. The installed compiler supports Swift 6, but this checkout does not yet build in strict Swift 6 mode.
- Review existing uncommitted UI changes against this specification before retaining, changing or discarding them. No migration is authorized by this document alone.
