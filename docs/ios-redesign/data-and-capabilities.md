# Student app: data and capability inventory

Status: repository audit, 18 November 2026. This records code paths, not a live guarantee that an upstream service currently works or returns complete data. “Native” means an iOS client exists in this checkout, not that every operation or account has been verified live. Credentials for private services must remain on the device.

| Student need | Source and available data | iOS evidence | Python evidence and gap |
| --- | --- | --- | --- |
| Know when and where to attend | Alma timetable, room details, cancellation observations, term | `ios/Shared/Alma/AlmaClient.swift`, `AlmaClient+TimetableCancellations.swift`; cached lecture snapshot | `sdk/authenticated.py` `timetable_view`; cancellation coverage depends on Alma response and parser. Missing cancellation is not proof a lecture takes place. |
| Know what is due | Moodle actionable calendar entries; ILIAS tasks and exercise assignments | `UniversityPortalClient.swift`, `MoodleOnDeviceClient.swift`, `IliasOnDeviceClient.swift` and `StudyTaskCache.swift` | Python exposes additional assignment and quiz reads. ILIAS scans have course and item limits; absence is not proof of completion. |
| See course materials | ILIAS content and exercise links; Moodle course pages and activities | `IliasOnDeviceClient.swift` and native course screens; scope differs by service | Python `course_content`, `content`, and `course_detail`. Cross-service identity is not guaranteed; matching needs evidence or explicit confirmation. |
| Obtain official documents | Alma study-service report choices and document download | No native document client was found in `ios/Shared`; a browser link is not an in-app document integration | Python `studyservice_documents`, `download_studyservice_report`, and exam report methods. Port the observed flow and validate current forms before promising native download. |
| Check academic progress | Alma enrollment and exams; Moodle grades | `UniversityGradesClient.swift`, `AlmaClient.swift` | Python Alma exams/enrollments and Moodle grades. Distinguish official transcript from displayed estimates and partial grade data. |
| Read university updates | University mail, Alma messages and Moodle notifications | Mail services in `ios/TueAPI/Services/Mail`; Alma portal messages client | Python mail and Moodle notifications. An unread count is not an importance or action classification. |
| Find courses and modules | Alma module descriptions, offering search; ILIAS/Moodle search | Native current-lecture and existing course browsing screens; do not assume Python search parity | Python `PublicAlmaApi`, authenticated `course_offerings`, ILIAS and Moodle search. Module records do not prove a current offering or eligibility. |
| Find campus resources | Canteens, buildings, seating, sports and KuF occupancy | `BackendClient+CampusFood.swift`, `SeatfinderClient.swift`, `KufOccupancyClient.swift`, campus views | Python campus APIs, sports offers and anny availability. Source coverage and freshness vary. |
| Find people, recordings and opportunities | University directory, Talks, TIMMS recordings, Praxisportal | Directory, Talks and Praxisportal clients exist; review each screen before promising parity | Python public clients for directory, Talks, TIMMS and Praxisportal. |
| Act on a course or assignment | Registration, joining, submissions, quizzes, forums | Some native Alma course-registration support; do not assume all Python writes are ported | Python includes review/write flows with different confirmation and verification properties. Show target and effects before writes; unknown result requires inspection. |
| Reach beyond the app | Housing, library account, residence, finance, university services | No general first-party account integration established here | `docs/student-services-research-2026-11-13.md` documents leads, not an implemented or currently verified capability. |

## Native surfaces and operating constraints

- The repository contains a lecture Home Screen widget, a rectangular Lock Screen widget, a KuF widget and a lecture Live Activity. Current uncommitted work also adds inline and circular lecture widgets; treat it as a draft, not a validated shipped feature.
- Widgets read a local app-group cache. WidgetKit determines actual refresh timing. Background refresh is best effort, not a live guarantee.
- The app supports iOS 17 and later according to `ios/project.yml`; inspect the deployment decision again before implementation.
- Credentials live in Keychain for native private flows. Some public content uses a backend; do not route student passwords through hosted services.
- Locally cached private information can be stale. Each card or source needs a meaningful freshness and error state, including partial failures.
- Python contains more capabilities than native iOS. Port request and parser contracts where required; an available Python method is not evidence that the phone can already perform it.

## Further verification before building

1. Check representative student accounts, faculties and course formats for completeness and terminology, with explicit consent for private data.
2. Confirm document report types, fresh Alma form state and safe download behavior using the Python implementation as a reference.
3. Audit cancellation sources, freshness and deduplication; preserve source and uncertainty.
4. Define source-specific timestamps, limits and failed-source presentation before building a merged attention feed.
5. Validate widget, Live Activity and notification timing on physical devices; do not claim real-time behavior from simulator builds.
