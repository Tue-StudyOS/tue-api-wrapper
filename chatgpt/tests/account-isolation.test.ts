import assert from "node:assert/strict";
import { test } from "node:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { StateStore } from "../src/auth/state-store.js";
import { SidecarRelay } from "../src/relay/relay.js";
import { studyContext, type StudyContext } from "../src/request-context.js";
import { storeAction, consumePendingAction } from "../src/tools/critical-action-store.js";
import { fetchPortalJson } from "../src/backend-http.js";
import { validateRelayRequest } from "../src/relay/contract.js";
import { currentStudyTerm } from "../src/terms.js";

test("a confirmation survives restart, belongs to one student, and cannot replay", () => {
  const directory = mkdtempSync(join(tmpdir(), "tue-release-")), path = join(directory, "state.sqlite");
  const relay = new SidecarRelay(); let store = new StateStore(path);
  const context = (userId: string): StudyContext => ({ userId, store, relay, origin: new URL("https://study.example") });
  try {
    const action = studyContext.run(context("alice"), () => storeAction({ kind: "ilias_add_favorite", portal: "ILIAS", title: "Selected course", actionLabel: "Add favorite", targetUrl: "https://ovidius.uni-tuebingen.de/course", endpoint: "/api/ilias/favorites", method: "POST", sideEffects: [], requiredInputs: [] }, { kind: "ilias_add_favorite", url: "https://ovidius.uni-tuebingen.de/course" }));
    store.close(); store = new StateStore(path);
    studyContext.run(context("bob"), () => assert.throws(() => consumePendingAction(action.intent.id, action.token), /no longer valid/));
    studyContext.run(context("alice"), () => {
      assert.deepEqual(consumePendingAction(action.intent.id, action.token).intent, action.intent);
      assert.throws(() => consumePendingAction(action.intent.id, action.token), /no longer valid/);
    });
  } finally { store.close(); relay.close(); rmSync(directory, { recursive: true }); }
});
test("relay routes responses to the requesting student and accepts concurrent reads", async () => {
  const relay = new SidecarRelay(), store = new StateStore(":memory:");
  const context = (userId: string): StudyContext => ({ userId, store, relay, origin: new URL("https://study.example") });
  try {
    const delivered: string[] = [];
    relay.poll("alice", job => {
      if (!job) return;
      delivered.push(job.id);
      assert.equal(relay.complete("bob", job.id, { status: 200, contentType: "application/json", data: Buffer.from('{"user":"bob"}').toString("base64") }), false);
      relay.complete("alice", job.id, { status: 200, contentType: "application/json", data: Buffer.from('{"user":"alice"}').toString("base64") });
    });
    const first = studyContext.run(context("alice"), () => fetchPortalJson<{ user: string }>("/api/ilias/tasks"));
    const second = studyContext.run(context("alice"), () => fetchPortalJson<{ user: string }>("/api/ilias/memberships"));
    relay.poll("alice", job => {
      assert.ok(job); delivered.push(job.id);
      relay.complete("alice", job.id, { status: 200, contentType: "application/json", data: Buffer.from('{"user":"alice"}').toString("base64") });
    });
    assert.deepEqual(await Promise.all([first, second]), [{ user: "alice" }, { user: "alice" }]);
    assert.equal(delivered.length, 2);
    await assert.rejects(studyContext.run(context("bob"), () => fetchPortalJson("/api/ilias/tasks")), /disconnected/);
  } finally { relay.close(); store.close(); }
});
test("relay rejects arbitrary backend paths, redirects, and unapproved mutations", () => {
  for (const path of ["https://attacker.invalid/api/search", "//attacker.invalid/api/search", "/api/admin", "/api/../admin", "/api/search#fragment"]) assert.throws(() => validateRelayRequest({ path, method: "GET" }));
  assert.throws(() => validateRelayRequest({ path: "/api/mail/inbox", method: "POST" }));
  assert.doesNotThrow(() => validateRelayRequest({ path: "/api/alma/documents/current", method: "GET" }));
});
test("semester boundaries use Berlin dates and continue across years", () => {
  for (const [timestamp, term] of [["2026-03-31T21:59:00Z", "Winter 2025/26"], ["2026-03-31T22:00:00Z", "Sommer 2026"], ["2026-09-30T21:59:00Z", "Sommer 2026"], ["2026-09-30T22:00:00Z", "Winter 2026/27"], ["2027-02-01T00:00:00Z", "Winter 2026/27"]]) assert.equal(currentStudyTerm(new Date(timestamp)), term);
});
test("oversized JSON responses fail explicitly and concurrent PDF delivery is bounded", async () => {
  const relay = new SidecarRelay();
  try {
    relay.poll("alice", job => {
      assert.ok(job);
      relay.complete("alice", job.id, { status: 200, contentType: "application/json", data: "A".repeat(1_400_000) });
    });
    await assert.rejects(relay.request("alice", { path: "/api/ilias/tasks", method: "GET" }), /too much data/);
    const jobs = [];
    for (let i = 0; i < 5; i++) relay.poll(`pdf-${i}`, () => {});
    for (let i = 0; i < 4; i++) jobs.push(relay.request(`pdf-${i}`, { path: "/api/alma/documents/current", method: "GET" }));
    assert.throws(() => relay.request("pdf-4", { path: "/api/alma/documents/current", method: "GET" }), /delivery is busy/);
    const settled = Promise.allSettled(jobs);
    relay.close();
    assert.ok((await settled).every(result => result.status === "rejected"));
  } finally { relay.close(); }
});
