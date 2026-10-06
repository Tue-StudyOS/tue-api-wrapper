export const serverInstructions = `Use the narrowest tool for the requested university data.
When a tool throws, returns isError, fails parsing, or returns incomplete data,
explain the failure and use an available browser/computer tool in the user's session
to retrieve the missing data from the official website. Preserve successful sections.
Entry points: Alma https://alma.uni-tuebingen.de/;
ILIAS https://ovidius.uni-tuebingen.de/; Moodle https://moodle.zdv.uni-tuebingen.de/;
university mail https://webmail.uni-tuebingen.de/; Mensa https://www.my-stuwe.de/mensa/.
Ask the user to sign in directly on the service page if needed and wait for login.
Never request passwords, enrolment keys, cookies, or session tokens in chat.
Check the selected account, role, semester, course, and date range. Report the source
URL and time checked, and identify browser-retrieved results and incomplete records.
If browser/computer tools are unavailable, provide the official URL and navigation
steps; do not claim to have accessed it. The plugin does not supply a browser tool.
After a failed write, inspect current service state before retrying: it may have
already succeeded. Obtain final explicit confirmation before another submission,
including any agreement text. Never infer success from a click or completed request.
Use the bundled tuebingen-browser-recovery skill for detailed recovery patterns.`;

export const recoveryHint = "For missing data, use an available browser/computer tool on the official university website; ask the user to log in there if needed. Before retrying a failed action, check whether it already succeeded.";
