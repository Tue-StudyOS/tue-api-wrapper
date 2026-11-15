# Live course search and portal observations

Date: 15 November 2026. Observations were made with an authorized student
account and the user's university VPN. No session tokens, search-result text,
or personal records are recorded in this document.

## Search validation

- Alma, ILIAS and Moodle authenticated through their existing local clients.
- A read-only `Machine Learning` search returned results from each system. The
  combined `tue-study course-search` command returned a successful source status
  for each service. This is one query on one account, not complete coverage.
- Raw search form/results were tested for Alma and ILIAS and raw results for
  Moodle. The `raw_alma_course_search`, `raw_ilias_search`, and
  `raw_moodle_search` MCP tools returned HTTP 200 and nonempty bodies.
- The Alma search POST returned a same-flow redirect before the results page.
  The raw client now follows bounded, same-host, same-path, same-flow redirects.
- ILIAS search exceeded an eight-second diagnostic timeout but succeeded with
  the normal client timeout. Slow searches do not establish a parser failure.
- Without the VPN, initial attempts timed out. After the existing university
  profile connected, all three services responded. This does not prove VPN is
  the only possible reason for a timeout or that it is required in all networks.

## Additional observed surfaces

- Moodle's signed-in home page links to MoodlePro, a separate service for
  non-semester courses. An attempted browser connection to its home page
  returned `ERR_ADDRESS_UNREACHABLE`; login, catalogue coverage and integration
  are unverified. Do not present MoodlePro as already covered.
- Moodle's home page links to a course-request page for teachers and a tag
  search page. The course-request route was already noted in
  [Moodle discovery](moodle-discovery.md); neither user capability nor a write
  contract was tested in this session.
- The ILIAS home page displays a permissions error for one requested object
  alongside the repository categories. The visible error does not establish
  that the account lacks access to all ILIAS courses.

These observations do not authorize course creation, registration, submission,
or other upstream changes. Future discovery should avoid persisting private
HTML, live cookies, request tokens, or account-specific identifiers.
