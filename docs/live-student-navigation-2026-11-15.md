# Live student portal navigation: 15 November 2026

This is a read-only observation of one signed-in student account, not an
exhaustive service inventory or an endpoint specification. Visibility and
features vary by account, course, permissions and semester. No registrations,
submissions, deletions, messages or quiz attempts were performed. Private account
values and session-specific URLs are intentionally omitted.

## Alma

**Mein Studium** leads to Studienplaner, Stundenplan, Belegungen, Leistungen,
Wahlfächer anmelden and Studienservice. The planner combines module planning,
course enrollment and exam registration. Belegungen shows enrollment information;
Leistungen shows academic results. The timetable displays personal events.

**Studienservice** has tabs for required documents, degree programmes, contact
details, payments and certificates/notices. The required-documents tab shows
document names and review status. Payments separates open bills from completed
payments and presents period, purpose, amount due, amount paid and detail
actions. A banner can show the re-registration state. Contact details and payment
values are sensitive; agents should fetch only what a task needs.

**Studienangebot** offers course search, events on a selected day, a hierarchical
course catalogue, module descriptions and applications. Daily events can be
searched using date, room or lecturer. A catalogue branch is not necessarily a
course; preserve the type and source link at every step.

Existing coverage includes timetable, notices, results, enrollments, search and
study-service document handling. The current [study-service model](../package/src/tue_api_wrapper/alma_studyservice_models.py)
contains tabs, reports and a banner, but has no typed payment or required-document
rows. Inspect actual forms and responses before building those readers; the UI
does not establish a stable standalone API.

## ILIAS

One observed path was **Veranstaltungen (Magazin) → semester → faculty → subject
→ instructor/category → course**. Some courses also appear directly under a
subject. The root includes research, external offerings and semester-independent
categories. The directory therefore needs typed nodes, pagination and source
links rather than an assumed fixed depth.

An observed course exposed **Inhalt**, **Info**, **Mitglieder** and
**Lernfortschritt**, plus a membership-ending action. The content included a
forum and tests. Forum listings exposed unread and last-post information. The
learning-progress page showed a mode and status categories: not started, in
progress, completed and failed. Progress can be manually controlled and is not
proof of exam admission or credit.

The wrapper already reads [ILIAS root, memberships, content, forum topics,
exercises and quiz metadata](../package/src/tue_api_wrapper/api_routes_ilias.py).
It also exposes memberships and a content reader through MCP. Recursive browsing,
full forum discussions and learning-progress details need further investigation;
do not assume first-level content is a complete course tree. One visited page
also displayed an object permission error alongside visible categories, so an
error must remain attached to the specific object.

## Moodle

The main navigation separates **Startseite**, **Dashboard** and **Meine Kurse**.
The dashboard presents a calendar and upcoming events. The course overview has
search, grouping, sorting and display controls; course cards can show a completion
percentage. Course pages contain sections, course information and activities,
with tabs such as participants and grades. One inspected course included an
announcements forum, an activity and externally hosted materials.

Useful observed path shapes, with identifiers omitted:

- `/my/` — dashboard; `/my/courses.php` — enrolled-course overview.
- `/calendar/view.php` — calendar; `/calendar/managesubscriptions.php` — import/export management.
- `/course/view.php?id=…` and `/course/section.php?id=…` — course and section views.
- `/mod/forum/view.php?id=…` — forum; other `/mod/…/view.php` paths identify activities.
- `/course/request.php` — teacher course requests; `/tag/search.php` — tag search.

These are browser routes observed in one instance, not promised stable APIs.
The wrapper already offers [dashboard, calendar, enrolled courses, categories,
course enrollment detail, grades, messages and notifications](../package/src/tue_api_wrapper/api_routes_moodle.py).
It does not establish that the enrollment-oriented course detail includes the
actual sections, activity instructions, attachments, submission status or
feedback. Those need separate investigation and typed readers.

## Cross-system course evidence

One Moodle course page explicitly linked to two Alma course records and to
other university course pages. A single learning-platform course can therefore
relate to multiple Alma records. Preserve each outgoing link, its label and its
source context as evidence for an agent; do not automatically merge records or
assume every course provides such a link. Inspect redirects and access
requirements before following external materials. URLs can contain sensitive
access tokens, so never put unredacted links in shared logs or documentation.

## Recommended next read-only work

1. **Course contents and evidence:** expose Moodle sections, activity links and
   course descriptions; extract explicit cross-system links with provenance.
   Check pagination, permissions and whether descriptions omit later sections.
2. **Assignment detail:** inspect Moodle assignment instructions, due dates,
   submission state and feedback without uploading or submitting anything.
   Distinguish these from calendar summaries and actual graded outcomes.
3. **ILIAS navigation and progress:** expose typed child objects and progress
   where available; preserve access errors and avoid unbounded traversal.
4. **Alma study service:** read required-document review and payment summaries,
   with precise source status and private local handling.
5. **Teacher discovery:** inspect authorized teaching views separately. A
   student-visible course-request link does not establish instructor access or
   the ability to manage courses.

See the [course-access request flows](agent-course-access.md). These observations
identify candidates; they do not validate the underlying request contracts.
