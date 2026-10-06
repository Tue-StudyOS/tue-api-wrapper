// Explicit test fixtures only. This server never accesses university systems.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
const intent = {
  id: "test-action", kind: "ilias_add_favorite", portal: "ILIAS", title: "Test favorite",
  actionLabel: "Add ILIAS favorite", targetUrl: "https://ilias.uni-tuebingen.de/",
  endpoint: "/api/ilias/favorites", method: "POST", sideEffects: ["Adds the selected course to favorites."],
  requiredInputs: [], preparedAt: new Date().toISOString(), expiresAt: new Date(Date.now() + 600000).toISOString(),
};
const dashboard = {
  generatedAt: "2026-10-06T08:00:00Z", termLabel: "Winter 2026/27",
  hero: { title: "Study Hub", subtitle: "Test fixture — no university account connected." },
  metrics: [{ label: "Upcoming events", value: 1 }],
  agenda: { exportUrl: "", items: [{ summary: "Computer Science lecture", start: "2026-10-07T08:15:00Z", end: null, location: "Lecture room", description: null }] },
  study: { selectedTerm: "Winter 2026/27", message: null, passedExamCount: 0, trackedCredits: 0, currentSemesterCredits: null },
  documents: { reports: [], currentDownloadAvailable: false, currentDownloadUrl: null }, exams: [],
  ilias: { memberships: [], tasks: [] }, talks: { available: false, error: "Talks unavailable in this test." },
};
const views = {
  dashboard: { view: "dashboard", dashboard }, action: { view: "critical-action", intent },
  error: { view: "error", message: "University access was denied. Check your account connection." },
  mensa: { view: "mensa", date: "2026-10-06", canteens: [], matched_menu_count: 0, requested_canteen_ids: [], requested_icons: [] },
};
const script = readFileSync(new URL("../web/dist/widget.js", import.meta.url), "utf8");
const css = readFileSync(new URL("../web/dist/widget.css", import.meta.url), "utf8");
createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:8091");
  const view = url.searchParams.get("view") ?? "dashboard";
  const theme = url.searchParams.get("theme") === "dark" ? "dark" : "light";
  const result = views[view] ?? views.error;
  if (url.pathname === "/widget") {
    const extension = url.searchParams.get("mode") === "bridge" ? "" : `<script>
      window.openai = { theme: ${JSON.stringify(theme)}, requestDisplayMode: async ({mode}) => ({mode}), toolOutput: ${JSON.stringify(result)}, toolResponseMetadata: { confirmationToken: 'test-secret' },
        setWidgetState: () => {}, notifyIntrinsicHeight: () => {},
        callTool: async () => ({ isError: true, structuredContent: { error: 'The study service timed out. Try again.' } }) };
    </script>`;
    res.writeHead(200, { "content-type": "text/html" }).end(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${css}</style></head><body data-template="${view === "action" ? "action" : "dashboard"}"><div id="root"></div>${extension}<script type="module">${script}</script></body></html>`);
    return;
  }
  res.writeHead(200, { "content-type": "text/html" }).end(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0"><iframe title="Study widget" src="/widget${url.search}" style="border:0;width:100%;height:95vh"></iframe><script>
  let calls = 0;
  window.addEventListener('message', event => {
    const frame = document.querySelector('iframe');
    if (event.source !== frame.contentWindow) return;
    const message = event.data;
    if (message.method === 'ui/initialize') {
      event.source.postMessage({jsonrpc:'2.0',id:message.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'test-host',version:'1'},hostCapabilities:{},hostContext:{theme:${JSON.stringify(theme)},displayMode:'inline'}}}, '*');
    } else if (message.method === 'ui/notifications/initialized') {
      event.source.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{structuredContent:${JSON.stringify(result)},_meta:{confirmationToken:'test-secret'}}}, '*');
    } else if (message.method === 'ui/request-display-mode') {
      event.source.postMessage({jsonrpc:'2.0',id:message.id,result:{mode:message.params.mode}}, '*');
    } else if (message.method === 'ui/notifications/size-changed') {
      frame.style.height = message.params.height + 'px';
    } else if (message.method === 'tools/call') {
      document.body.dataset.calls = String(++calls);
      const name = message.params.name;
      const result = name === 'cancel_critical_action' ? {structuredContent:{status:'cancelled'}}
        : name === 'confirm_critical_action' ? {structuredContent:{status:'completed',intent:${JSON.stringify(intent)},result:{status:'success',message:'Fixture action completed.',finalUrl:null,raw:{}}}}
        : {isError:true,structuredContent:{error:'The study service timed out. Try again.'}};
      setTimeout(() => event.source.postMessage({jsonrpc:'2.0',id:message.id,result}, '*'), 200);
    } else if (message.id) {
      event.source.postMessage({jsonrpc:'2.0',id:message.id,result:{}}, '*');
    }
  });
  </script></body></html>`);
}).listen(8091, "127.0.0.1", () => console.log("Fixture host: http://127.0.0.1:8091/?mode=bridge&view=dashboard"));
