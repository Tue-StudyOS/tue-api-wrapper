import assert from "node:assert/strict";
import { test } from "node:test";

const listeners = new Map<string, Array<(event: any) => void>>();
const parent = {};
const variables = new Map<string, string>();
const element = { dataset: {} as Record<string, string>, style: { setProperty: (key: string, value: string) => variables.set(key, value) } };
Object.defineProperty(globalThis, "document", { value: { documentElement: element }, configurable: true });
Object.defineProperty(globalThis, "window", { value: {
  parent, openai: { callTool: () => {}, theme: "light", displayMode: "inline" },
  addEventListener: (name: string, listener: (event: any) => void) => listeners.set(name, [...(listeners.get(name) ?? []), listener]),
}, configurable: true });
const { connectHostAppearance } = await import("../web/src/host-appearance.js");
const modes: boolean[] = [];
connectHostAppearance((expanded) => modes.push(expanded));
function receive(params: object, source: object = parent) {
  for (const listener of listeners.get("message") ?? []) listener({ source, data: {
    jsonrpc: "2.0", method: "ui/notifications/host-context-changed", params,
  } });
}
test("host theme, style tokens and fullscreen updates apply together", () => {
  assert.equal(element.dataset.theme, "light");
  receive({ theme: "dark", displayMode: "fullscreen", styles: { variables: {
    "--color-text-primary": "#f5f5f5", "--font-sans": "system-ui", "unrelated": "ignored",
  } } });
  assert.equal(element.dataset.theme, "dark");
  assert.equal(variables.get("--color-text-primary"), "#f5f5f5");
  assert.equal(variables.get("--font-sans"), "system-ui");
  assert.equal(variables.has("unrelated"), false);
  assert.equal(modes.at(-1), true);
});
test("partial updates preserve display mode and foreign frames cannot change appearance", () => {
  const count = modes.length;
  receive({ theme: "light" });
  assert.equal(modes.length, count);
  receive({ theme: "dark", displayMode: "inline" }, {});
  assert.equal(element.dataset.theme, "light");
  assert.equal(modes.at(-1), true);
  receive({ displayMode: "inline" });
  assert.equal(modes.at(-1), false);
});
