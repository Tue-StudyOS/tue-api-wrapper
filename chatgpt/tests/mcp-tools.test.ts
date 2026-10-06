import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createServer } from "node:http";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createAppServer } from "../src/study-server.js";

let writeCount = 0;
const backend = createServer((req, res) => {
  if (req.url === "/api/search?query=fixture") {
    res.end(JSON.stringify({ results: [{ id: "fixture", title: "Selected course", url: "https://alma.uni-tuebingen.de/", text: "Public description" }] }));
  } else if (req.url === "/api/items/fixture") {
    res.end(JSON.stringify({ id: "fixture", title: "Selected course", url: "https://alma.uni-tuebingen.de/", text: "Public description" }));
  } else if (req.url?.startsWith("/api/ilias/favorites")) {
    writeCount++;
    res.end(JSON.stringify({ status: "submitted", message: null, final_url: "https://ilias.uni-tuebingen.de/" }));
  } else res.writeHead(503).end("private upstream error");
});
const client = new Client({ name: "release-tests", version: "1" });
const server = createAppServer();
const originalBase = process.env.PORTAL_API_BASE_URL;
before(async () => {
  await new Promise<void>((resolve) => backend.listen(0, "127.0.0.1", resolve));
  const address = backend.address();
  assert.ok(address && typeof address === "object");
  process.env.PORTAL_API_BASE_URL = `http://127.0.0.1:${address.port}`;
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  assert.match(client.getInstructions() ?? "", /https:\/\/alma.uni-tuebingen.de\//);
  assert.match(client.getInstructions() ?? "", /wait for login/);
  await client.listTools();
});
after(async () => {
  await client.close();
  await server.close();
  backend.closeAllConnections();
  await new Promise<void>((resolve) => backend.close(() => resolve()));
  if (originalBase === undefined) delete process.env.PORTAL_API_BASE_URL;
  else process.env.PORTAL_API_BASE_URL = originalBase;
});

const calls: Record<string, Record<string, unknown>> = {
  search: { query: "Computer Science" }, fetch: { id: "selected-id" },
  get_study_snapshot: {}, get_upcoming_schedule: {}, get_current_tasks: {}, get_current_grades: {},
  get_learning_spaces: {}, get_documents_summary: {}, get_mensa_food_plan: {},
  get_mail_inbox: {}, get_mail_message: { uid: "123" }, get_course_catalog_filters: {},
  search_courses: { query: "Neural Data Science" }, search_course_offerings: {},
  get_course_detail: { url: "https://alma.uni-tuebingen.de/detail" },
  get_combined_course_detail: { title: "Computer Science" }, get_study_planner: {},
  search_learning_spaces: { term: "Computer Science" }, inspect_learning_space: { target: "crs_123" },
  show_dashboard: {}, list_documents: {},
  prepare_alma_course_registration: { url: "https://alma.uni-tuebingen.de/detail" },
  prepare_ilias_waitlist_join: { url: "crs_123" }, prepare_moodle_course_enrolment: { courseId: 123 },
};
for (const [name, args] of Object.entries(calls)) {
  test(`${name} reports service failure as an MCP error`, async () => {
    const result = await client.callTool({ name, arguments: args });
    assert.equal(result.isError, true, name);
    assert.doesNotMatch(JSON.stringify(result), /private upstream error/);
  });
}
test("all advertised tools have explicit safety hints and valid resource links", async () => {
  const { tools } = await client.listTools();
  const { resources } = await client.listResources();
  const uris = new Set(resources.map((resource) => resource.uri));
  for (const tool of tools) {
    assert.ok(tool.outputSchema, `${tool.name} output schema`);
    for (const hint of ["readOnlyHint", "openWorldHint", "destructiveHint"] as const) {
      assert.equal(typeof tool.annotations?.[hint], "boolean", `${tool.name}.${hint}`);
    }
    const ui = tool._meta?.ui as { resourceUri?: string; visibility?: string[] } | undefined;
    if (ui?.resourceUri) assert.ok(uris.has(ui.resourceUri), tool.name);
  }
  for (const name of ["confirm_critical_action", "cancel_critical_action"]) {
    const tool = tools.find((value) => value.name === name);
    assert.deepEqual((tool?._meta?.ui as { visibility?: string[] }).visibility, ["app"]);
  }
});
test("resource read includes runnable widget HTML", async () => {
  const result = await client.readResource({ uri: "ui://study-hub/dashboard-v8.html" });
  assert.equal(result.contents[0].mimeType, "text/html;profile=mcp-app");
  assert.match(String(result.contents[0].text), /id="root"/);
});
test("invalid inputs and missing course identifiers return errors", async () => {
  for (const [name, args] of [["get_current_tasks", { limit: 100 }], ["get_combined_course_detail", {}], ["get_mail_message", {}]] as const) {
    const result = await client.callTool({ name, arguments: args });
    assert.equal(result.isError, true);
  }
});


test("search and fetch return standard JSON text and validated structured results", async () => {
  const search = await client.callTool({ name: "search", arguments: { query: "fixture" } });
  assert.notEqual(search.isError, true);
  assert.deepEqual(JSON.parse((search.content as Array<{ text: string }>)[0].text), {
    results: [{ id: "fixture", title: "Selected course", url: "https://alma.uni-tuebingen.de/" }],
  });
  const fetched = await client.callTool({ name: "fetch", arguments: { id: "fixture" } });
  assert.equal(JSON.parse((fetched.content as Array<{ text: string }>)[0].text).text, "Public description");
});

test("prepare, cancel and confirm have separate effects and reject replay", async () => {
  const prepare = async () => {
    const result = await client.callTool({ name: "prepare_ilias_add_favorite", arguments: { url: "https://ilias.uni-tuebingen.de/course" } });
    assert.notEqual(result.isError, true);
    return { intentId: (result.structuredContent as { intent: { id: string } }).intent.id, confirmationToken: String(result._meta?.confirmationToken) };
  };
  const cancelled = await prepare();
  assert.equal(writeCount, 0);
  assert.notEqual((await client.callTool({ name: "cancel_critical_action", arguments: cancelled })).isError, true);
  assert.equal((await client.callTool({ name: "confirm_critical_action", arguments: cancelled })).isError, true);
  assert.equal(writeCount, 0);
  const confirmed = await prepare();
  assert.notEqual((await client.callTool({ name: "confirm_critical_action", arguments: confirmed })).isError, true);
  assert.equal(writeCount, 1);
  assert.equal((await client.callTool({ name: "confirm_critical_action", arguments: confirmed })).isError, true);
  assert.equal(writeCount, 1);
});
