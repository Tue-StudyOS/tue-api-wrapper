# Forum and quiz access

These tools use the signed-in user's account. Forum content, quiz questions,
answers, URLs and raw responses may contain private data. Do not write them to
shared logs. A read may update Moodle or ILIAS read indicators; opening an
ILIAS post editor may initialize a draft.

The Moodle quiz request flow follows the observed view form and the upstream
[attempt form renderer](https://github.com/moodle/moodle/blob/MOODLE_404_STABLE/mod/quiz/classes/output/renderer.php)
and [attempt processor](https://github.com/moodle/moodle/blob/MOODLE_404_STABLE/mod/quiz/processattempt.php).
Deployed versions and question plugins may differ.

## Forum reads

```bash
tue study moodle-forum --target 12345 --page 0
tue study moodle-discussion --target 23456
tue study ilias-forum --target frm/12345
tue study ilias-thread --target 'https://ovidius.uni-tuebingen.de/ilias.php?...'
```

MCP equivalents are `study_moodle_forum`, `study_moodle_discussion`,
`study_ilias_forum` and `study_ilias_thread`. Moodle forum IDs are course
activity IDs; Moodle discussion IDs are the `d` parameter in discussion links.
ILIAS thread targets must be the university's `viewThread` URL returned by the
topic list. Read results reflect the visible page, not necessarily every page.
Use Moodle `page` to request other forum pages. Pagination markers vary by
platform, so an absent `next_url` is not proof of completeness. ILIAS thread
pagination is not yet exposed.

## Forum posts

Enable the opt-in MCP group using `tue mcp --service forum-write`, or reinstall
the package to get `tue forum`. Review requires the exact target, subject and
plain-text message. Publish requires the review hash and explicit confirmation.
For Moodle, `new` targets a forum activity ID and `reply` targets a post ID.
For ILIAS, `new` targets `frm/<id>`; `reply` targets the ILIAS thread URL and
requires its parent post ID.

```bash
tue forum review --service moodle --mode new --target 12345 --subject 'Question' --message 'My question'
tue forum publish --service moodle --mode new --target 12345 --subject 'Question' --message 'My question' --review-sha256 <hash> --confirm
tue forum review --service ilias --mode reply --target '<thread-url>' --parent-id 456 --subject 'Re: Question' --message 'My reply'
```

The MCP tools are `moodle_forum_review`, `moodle_forum_publish`,
`ilias_forum_review` and `ilias_forum_publish`. Attachments, editing, deleting,
and choosing a different group or posting identity are not supported. The
writers verify a returned post identifier and message when the platform's
redirect exposes one. If either platform returns `unknown` or a timeout,
inspect the forum before retrying; the post may already exist. Posting has only
been tested with controlled responses; live forms were inspected, but no post
was sent during development.

## Quiz reads and actions

`tue study moodle-quiz --target 12345` and MCP `study_moodle_quiz` read the
quiz overview without starting. An existing Moodle attempt page can be read
with `tue study moodle-attempt --target <attempt-id> --page 0` or
`study_moodle_quiz_attempt`. Supported fields are basic radio, checkbox, text,
textarea and select controls. Other question types fail explicitly. The result
only covers the visible page. Existing ILIAS quiz metadata remains available
via `authenticated_ilias_quiz` and `authenticated_ilias_quiz_deadlines`.

The opt-in `quiz-write` MCP group and `tue quiz` CLI expose Moodle start,
answer-save and finish as separate review and confirmed-write operations.
Starting may consume an attempt and start a timer; finishing submits answers
and can be irreversible. Review outputs contain hashes that bind the action to
the visible quiz state. Answer maps use the exposed field names and lists of
values, for example `{"q123:1_answer":["0"]}`. Moodle can change question
state or impose time limits between requests. These operations have been tested
only with controlled responses, not with a live attempt. A saved receipt means
that the reread fields matched, not that an answer is correct. Finish reports
`unknown` unless Moodle's review page exposes a recognized finished state.

```bash
tue quiz review-start --target 12345
tue quiz start --target 12345 --review-sha256 <hash> --confirm
tue study moodle-attempt --target <attempt-id> --page 0
tue quiz review-answers --target <attempt-id> --page 0 --answers-json '{"q123:1_answer":["0"]}'
tue quiz save-answers --target <attempt-id> --page 0 --answers-json '{"q123:1_answer":["0"]}' --review-sha256 <hash> --confirm
tue quiz review-finish --target <attempt-id>
tue quiz finish --target <attempt-id> --review-sha256 <hash> --confirm
```

ILIAS `review-start` and `start` can request the observed fixed-question test
start action. The start request returns `unknown` because its completion flow
has not been verified. For an **existing** attempt, the tools below resume it,
read the current question, save a reviewed answer, or review and confirm finish:

```bash
tue quiz read --service ilias --target 12345
tue quiz review-answers --service ilias --target 12345 --answers-json '{"multiple_choice_result42":["1"]}'
tue quiz save-answers --service ilias --target 12345 --answers-json '{"multiple_choice_result42":["1"]}' --review-sha256 <hash> --confirm
tue quiz review-finish --service ilias --target 12345
tue quiz finish --service ilias --target 12345 --review-sha256 <hash> --confirm
```

MCP exposes `ilias_quiz_question`, `ilias_quiz_review_answers`,
`ilias_quiz_save_answers`, `ilias_quiz_review_finish`, and `ilias_quiz_finish`
through the opt-in `quiz-write` group. The target is the ILIAS test reference
ID, not a Moodle-style attempt ID. Opening a question resumes an existing
attempt and can restart its timer or update question state; it will not follow a
start action. The reader supports the current question only, for single-choice,
multiple-choice, and text questions. It does not navigate between questions or
support other question types. Saving may lock an answer or trigger feedback.

Finish is supported only when ILIAS exposes a direct finish action and its
confirmation modal. Tests that require a question overview or another preflight
step fail without bypassing it. The finish receipt reports `finished` only when
the completed-attempt count increases by one; otherwise it reports `unknown`.
The answer save reports `unverified` even if reread values match: ILIAS can
redisplay submitted values after an error. Inspect ILIAS before retrying either
action. All ILIAS question, save and finish behavior was tested only with
controlled fixtures derived from upstream ILIAS 10 source, never a live attempt.
Question templates or local university changes may differ.

## Raw recovery

Enable MCP `raw` and use `raw_interaction_page`, or call, for example:

```bash
tue study raw-interaction --service moodle --kind discussion --target 23456
tue study raw-interaction --service moodle --kind attempt --target 34567 --page 0
tue study raw-interaction --service ilias --kind discussion --target '<thread-url>'
```

Raw reads return unredacted HTML and do not follow redirects. They may contain
active session tokens. Never publish them or save them to shared files.
