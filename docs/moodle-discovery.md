# Moodle Discovery From HAR

Source capture: `moodle.zdv.uni-tuebingen.de.har`

Session shape observed in the HAR:

- Shibboleth login into Moodle
- Moodle home page
- Dashboard at `/my/`
- My courses page at `/my/courses.php`
- Course category browsing at `/course/index.php?categoryid=...`
- Course self-enrol preview at `/enrol/index.php?id=1559`
- Course request page at `/course/request.php?categoryid=0`

This HAR is valuable because it reflects a normal student session instead of admin traffic. The most useful additions are the endpoints that back dashboard awareness, course discovery, and enrolment.

## Existing gap

This discovery note predates the current Moodle client. Check the SDK and MCP documentation for implemented coverage.

## High-value features to add first

### 1. Moodle dashboard snapshot

Why it matters:

- This is the student landing view.
- It combines upcoming action items, recent learning context, and enrolled courses.
- It maps well to the existing "study snapshot" idea already used elsewhere in the repo.

Verified endpoints:

- `GET /my/`
- `POST /lib/ajax/service.php?sesskey=...&info=core_calendar_get_action_events_by_timesort`
- `POST /lib/ajax/service.php?sesskey=...&info=block_recentlyaccesseditems_get_recent_items`
- `POST /lib/ajax/service.php?sesskey=...&info=core_course_get_enrolled_courses_by_timeline_classification`

Observed request contracts:

- `core_calendar_get_action_events_by_timesort`
  - args: `limitnum`, `timesortfrom`, `timesortto`, `limittononsuspendedevents`
- `block_recentlyaccesseditems_get_recent_items`
  - args: `limit`
- `core_course_get_enrolled_courses_by_timeline_classification`
  - args: `offset`, `limit`, `classification`, `sort`, `customfieldname`, `customfieldvalue`, `requiredfields`
  - observed required fields: `id`, `fullname`, `shortname`, `showcoursecategory`, `showshortname`, `visible`, `enddate`

Recommended product feature:

- Add a Moodle dashboard endpoint that returns:
  - upcoming deadlines and calendar actions
  - recently accessed courses/resources
  - enrolled course list with visibility and end date

Suggested wrapper surface:

- `GET /api/moodle/dashboard`
- `GET /api/moodle/events`
- `GET /api/moodle/recent-items`
- `GET /api/moodle/courses`

### 2. Course catalog and category browsing

Why it matters:

- Students browse categories before enrolment.
- This is the clearest Moodle equivalent to course discovery.
- The HAR shows both full page navigation and lazy category expansion.

Verified endpoints:

- `GET /course/index.php?categoryid=...`
- `POST /course/category.ajax.php`

Observed request contract for `POST /course/category.ajax.php`:

- form fields: `categoryid`, `depth`, `showcourses`, `type`
- observed sample payload:
  - `categoryid=232`
  - `depth=2`
  - `showcourses=5`
  - `type=0`

Recommended product feature:

- Add a Moodle category explorer that can:
  - list child categories
  - show a small preview set of courses per category
  - support progressive expansion in the UI

Suggested wrapper surface:

- `GET /api/moodle/categories/{category_id}`
- `GET /api/moodle/categories/{category_id}/courses`

### 3. Course enrolment preview and self-enrol

Why it matters:

- The HAR includes a concrete pre-enrolment workflow.
- This is directly actionable for students.
- It exposes useful metadata even before enrolment.

Verified endpoints:

- `GET /course/view.php?id=1559`
- `GET /enrol/index.php?id=1559`
- `POST /enrol/index.php`

Observed form contract for self-enrol:

- hidden fields: `id`, `instance`, `sesskey`, `_qf__13357_enrol_self_enrol_form`, `mform_isexpanded_id_selfheader`
- submit field: `submitbutton`
- observed page text: `Kein Einschreibekennwort notwendig`

Observed course metadata on enrol page:

- course title
- course summary
- teacher list
- self-enrol availability
- direct link to course view

Recommended product feature:

- Add a course detail endpoint that exposes:
  - title
  - summary
  - teachers
  - enrolment type
  - whether an enrolment key is required
  - whether self-enrol is available
- Optionally add a separate enrol action once read-only parsing is stable.

Suggested wrapper surface:

- `GET /api/moodle/course/{course_id}`
- `GET /api/moodle/course/{course_id}/enrolment`
- `POST /api/moodle/course/{course_id}/enrol`

## Medium-value features worth adding after the first pass

### 4. Full Moodle calendar view

Evidence:

- Verified link from the enrol page: `GET /calendar/view.php?view=month`
- Stronger evidence already exists via the dashboard AJAX event call.

Why it matters:

- Students care about deadlines and due dates more than generic portal content.

Recommended feature:

- Calendar aggregation beyond the limited dashboard window.

### 5. Grade overview

Evidence:

- Link discovered on the enrol page: `GET /grade/report/overview/index.php`
- Not directly requested during this HAR session, so this is an inference from a verified page link.

Why it matters:

- Grades are consistently high-value in student tooling.
- The existing repo already treats grades as a top-level dashboard concept for Alma.

Recommended feature:

- Moodle grade overview parsing, likely as a separate feature from dashboard events.

### 6. Moodle messages and notifications

Evidence:

- Verified links discovered on the enrol page:
  - `GET /message/index.php`
  - `GET /message/notificationpreferences.php`
  - `GET /message/output/popup/notifications.php`

Why it matters:

- Students miss deadline changes and course announcements when messaging is buried in Moodle.

Recommended feature:

- Read-only notifications and message summary support.

## Low-priority or non-student features seen in the HAR

These should not drive the first implementation pass:

- `tool_usertours_fetch_and_start_tour`
- `tool_usertours_complete_tour`
- `media_videojs_get_language`
- `tiny_autosave_resume_session`
- `lib/ajax/service-nologin.php` template and string loading
- raw Shibboleth request capture beyond what is needed for login
- `course/request.php`
  - observed in the session, but this looks more like course creation/request workflow than day-to-day student value

## Recommended implementation order

1. Moodle dashboard snapshot
2. Course catalog and category explorer
3. Course detail and enrolment preview
4. Grade overview
5. Messages and notifications
6. Optional self-enrol action

## Suggested contract shape

If we keep this aligned with the rest of the repo, the first Python client additions should be read-only:

- dashboard snapshot methods
- course category discovery methods
- course detail parsing methods
- enrolment status parsing methods

Then expose them in:

- FastAPI routes under `/api/moodle/...`
- `tue study` and the local MCP server

## Confidence notes

- High confidence:
  - dashboard events
  - recent items
  - enrolled courses
  - category browsing
  - enrolment preview
- Medium confidence:
  - full calendar
  - grade overview
  - messages and notifications
- Low confidence:
  - course request workflow as a student-facing feature
