# Submission package

Publisher: **Sebastian Boehler** (individual verification).
Support: **s.boehler@student.uni-tuebingen.de**.
The verified identity selected in the dashboard determines the directory's
publisher name. A separate Sunderlabs organization can own future company plugins.

## Generate the production ZIP

```sh
npm ci --workspaces=false
npm run check
npm test
npm run build
npm run release:package -- https://YOUR_PRODUCTION_HOST
```

The generator requires the real HTTPS origin. It writes `release/` with:

- `tuebingen-study-hub.zip`: portable `plugin.json`, production `mcp.json`,
  onboarding and browser recovery skills, original icon, and license.
- `tool-inventory.json`: 28 tools discovered from the actual server, with input
  and output schemas, safety hints, OAuth metadata and resource URIs.
- Deployment, review and submission instructions.

The ZIP contains exactly five positive and three negative review cases. The
generator includes no credentials, university data, `.env`, database, test
fixtures, dependency directory or source maps. Developer-only preview images
use labeled fixture data and are not public submission screenshots.

The repository's `plugin.json` is a source manifest. The generator fills all
four required public URLs in the production manifest. Never upload the source
folder as a ZIP: it intentionally lacks a production MCP URL. Include MCP in
the initial upload; OpenAI currently does not allow adding it to a skills-only
plugin after creation.

## External tasks after deployment

1. Complete individual publisher and domain verification in the Platform.
2. Verify all public URLs and actual ChatGPT OAuth/widget behavior over HTTPS.
3. Prepare a real permitted demo account. Keep its university sessions and
   local sidecar running throughout review. Reviewers enter the link password
   on the service login page and need no sidecar installation or MFA.
4. Enter reviewer access credentials in the secure dashboard form. Never put
   them in the ZIP, source manifest, video, logs or screenshots.
5. Record a walkthrough on the deployed plugin using permitted account data.
   Provide the reviewer-accessible recording URL through the dashboard.
6. Execute the five positive and three negative cases; retain actual outcomes.
7. Resolve automated package/MCP findings, then submit for review. Publication
   follows approval and a separate publisher decision.

University authorization and public-directory eligibility remain external
requirements. Current OpenAI guidelines restrict unofficial third-party
connectors; no approval or exception has been established for this integration.
Do not claim university endorsement or use its crest. The included icon is
original. These public terms and privacy pages describe current code behavior;
review the deployed operator's contact, retention and legal obligations before
publication.

References: [submission](https://developers.openai.com/plugins/deploy/submission),
[package structure](https://developers.openai.com/plugins/build/plugins),
[authentication](https://developers.openai.com/plugins/build/auth),
[review](https://developers.openai.com/plugins/deploy/app-review),
[plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines).
