import assert from "node:assert/strict";
import { test } from "node:test";
import { consumePendingAction, preparedResponse, storeAction } from "../src/tools/critical-action-store.js";
import type { CriticalActionPublicIntent } from "../src/types/actions.js";

const intent: Omit<CriticalActionPublicIntent, "id" | "preparedAt" | "expiresAt"> = {
  kind: "ilias_add_favorite", portal: "ILIAS", title: "Selected course",
  actionLabel: "Add favorite", targetUrl: "https://ilias.uni-tuebingen.de/course",
  endpoint: "/api/ilias/favorites", method: "POST", sideEffects: ["Adds favorite"], requiredInputs: [],
};
const command = { kind: "ilias_add_favorite" as const, url: intent.targetUrl! };

test("confirmation secret stays outside model-visible content", () => {
  const stored = storeAction(intent, command);
  const result = preparedResponse(stored);
  assert.equal(result._meta.confirmationToken, stored.token);
  assert.doesNotMatch(JSON.stringify({ structuredContent: result.structuredContent, content: result.content }), new RegExp(stored.token));
});
test("wrong token does not consume a valid intent", () => {
  const stored = storeAction(intent, command);
  assert.throws(() => consumePendingAction(stored.intent.id, "wrong"), /no longer valid/);
  assert.deepEqual(consumePendingAction(stored.intent.id, stored.token).intent, stored.intent);
});
test("consumed or cancelled intent cannot execute again", () => {
  const stored = storeAction(intent, command);
  consumePendingAction(stored.intent.id, stored.token);
  assert.throws(() => consumePendingAction(stored.intent.id, stored.token), /no longer valid/);
});
test("expired intent is rejected", () => {
  const stored = storeAction(intent, command);
  const originalNow = Date.now;
  try {
    Date.now = () => originalNow() + 601_000;
    assert.throws(() => consumePendingAction(stored.intent.id, stored.token), /no longer valid/);
  } finally { Date.now = originalNow; }
});
test("preparing never executes the upstream action", () => {
  const stored = storeAction(intent, command);
  assert.equal(stored.intent.kind, "ilias_add_favorite");
  // The HTTP MCP regression test asserts zero writes before confirmation.
});
