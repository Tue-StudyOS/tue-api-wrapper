# ILIAS quizzes (read-only)

- `GET /api/ilias/quiz?target=tst/5846588`: one quiz's Info metadata.
- `GET /api/ilias/course-quizzes?target=crs/5743244`: quizzes directly listed in a course.
- `GET /api/ilias/quiz-deadlines?course_limit=20&quiz_limit=50`: quiz metadata with course context across memberships.

Python SDK: `client.ilias.quiz(target)`, `course_quizzes(target)`, and `quiz_deadlines()`.
MCP: `authenticated_ilias_quiz` and `authenticated_ilias_quiz_deadlines`.

The existing assignment-deadlines endpoint still returns exercise assignments only.
Consumers collecting all deadlines must combine both endpoint responses.

`opens_at` and `closes_at` preserve ILIAS display strings, including relative dates.
They are not ISO timestamps. `completed_attempts` is null when ILIAS does not expose
the field, not zero. A completed attempt is not a passing score or proof of overall
exam admission. No attempt is started, answered or submitted by these methods.
Questions and saved answers are not exposed by this metadata reader.

Discovery covers directly listed tests, not nested folders or unpublished quizzes.
Authentication uses the existing local ILIAS client. No credentials or private
quiz responses should be included in logs or committed fixtures.
