import assert from "node:assert/strict";
import { test } from "node:test";

const messages: Array<{ id?: string; method: string; params?: unknown }> = [];
const listeners: Array<(event: { source: unknown; data: unknown }) => void> = [];
const parent = { postMessage: (value: typeof messages[number]) => { messages.push(value); } };
const fakeWindow = { parent, addEventListener: (_name: string, listener: typeof listeners[number]) => listeners.push(listener), openai: undefined as unknown };
Object.defineProperty(globalThis, "window", { value: fakeWindow, configurable: true });
const { callHostTool, connectBridge, readToolMetadata, requireToolContent, sendFollowUp, requestDisplayMode } = await import("../web/src/widget-bridge.js");
function receive(data: unknown, source = parent) { for (const listener of listeners) listener({ source, data }); }

test("initializes once and ignores messages from another frame", async () => {
  const connected = connectBridge();
  const init = messages.at(-1)!;
  assert.equal(init.method, "ui/initialize");
  assert.equal(connectBridge(), connected);
  receive({ jsonrpc: "2.0", id: init.id, result: {} }, {} as typeof parent);
  receive({ jsonrpc: "2.0", id: init.id, result: {} });
  await connected;
  assert.equal(messages.at(-1)?.method, "ui/notifications/initialized");
});
test("routes tool calls through the standard bridge and propagates failures", async () => {
  const result = callHostTool("get_current_tasks", { limit: 8 });
  await Promise.resolve();
  const call = messages.at(-1)!;
  assert.equal(call.method, "tools/call");
  receive({ jsonrpc: "2.0", id: call.id, result: { isError: true, content: [{ type: "text", text: "University access denied." }] } });
  await assert.rejects(result, /University access denied/);
});
test("keeps widget-only metadata from standard notifications", () => {
  receive({ jsonrpc: "2.0", method: "ui/notifications/tool-result", params: { _meta: { confirmationToken: "test-only" } } });
  assert.deepEqual(readToolMetadata(), { confirmationToken: "test-only" });
});
test("rejects empty and legacy error payloads instead of caching them", () => {
  assert.throws(() => requireToolContent({}), /no data/);
  assert.throws(() => requireToolContent({ structuredContent: { error: "Unavailable" } }), /Unavailable/);
  assert.throws(() => requireToolContent({ structuredContent: { view: "error", message: "Unavailable" } }), /Unavailable/);
  assert.deepEqual(requireToolContent({ structuredContent: { items: [] } }), { items: [] });
});
test("follow-up messages use MCP Apps role and content fields", async () => {
  const followup = sendFollowUp("Summarize these tasks.");
  await Promise.resolve();
  const call = messages.at(-1)!;
  assert.equal(call.method, "ui/message");
  assert.deepEqual(call.params, { role: "user", content: [{ type: "text", text: "Summarize these tasks." }] });
  receive({ jsonrpc: "2.0", id: call.id, result: {} });
  await followup;
});

test("fullscreen reflects the mode confirmed by the host", async () => {
  const change = requestDisplayMode("fullscreen");
  await Promise.resolve();
  const call = messages.at(-1)!;
  assert.equal(call.method, "ui/request-display-mode");
  assert.deepEqual(call.params, { mode: "fullscreen" });
  receive({ jsonrpc: "2.0", id: call.id, result: { mode: "inline" } });
  assert.equal(await change, "inline");
  const failed = requestDisplayMode("fullscreen");
  await Promise.resolve();
  receive({ jsonrpc: "2.0", id: messages.at(-1)!.id, error: { message: "Fullscreen unavailable." } });
  await assert.rejects(failed, /Fullscreen unavailable/);
});
