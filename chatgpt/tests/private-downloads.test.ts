import assert from "node:assert/strict";
import { test } from "node:test";
import { createServer } from "node:http";
import express from "express";
import { StateStore } from "../src/auth/state-store.js";
import { SidecarRelay } from "../src/relay/relay.js";
import { createDownloadTicket, downloadRoutes } from "../src/downloads.js";

test("private PDF tickets expire, are single-use and route through their owner's device", async () => {
  const store = new StateStore(":memory:"), relay = new SidecarRelay(), app = express();
  app.use("/downloads", downloadRoutes(store, relay));
  const server = createServer(app);
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address(); assert.ok(address && typeof address === "object");
  const origin = new URL(`http://127.0.0.1:${address.port}`);
  const context = { userId: "alice", store, relay, origin };
  store.put("user", "alice", true, Date.now() + 3600_000);
  try {
    const url = createDownloadTicket(context, "/api/alma/documents/current");
    assert.throws(() => createDownloadTicket(context, "https://attacker.invalid/file"), /unsupported/);
    relay.poll("alice", job => {
      assert.ok(job); assert.equal(job.path, "/api/alma/documents/current");
      const result = { status: 200, contentType: "application/pdf", data: Buffer.from("%PDF-1.7\nFixture test PDF").toString("base64") };
      assert.equal(relay.complete("bob", job.id, result), false);
      assert.equal(relay.complete("alice", job.id, result), true);
    });
    const response = await fetch(url);
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.match(await response.text(), /^%PDF-/);
    assert.equal((await fetch(url)).status, 410);
    const expired = createDownloadTicket(context, "/api/alma/documents/current");
    const originalNow = Date.now;
    try { Date.now = () => originalNow() + 121_000; assert.equal((await fetch(expired)).status, 410); }
    finally { Date.now = originalNow; }
  } finally {
    relay.close(); server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve())); store.close();
  }
});
test("download tickets never turn an HTML error into a PDF", async () => {
  const store = new StateStore(":memory:"), relay = new SidecarRelay(), app = express();
  app.use("/downloads", downloadRoutes(store, relay)); const server = createServer(app);
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address(); assert.ok(address && typeof address === "object");
  const origin = new URL(`http://127.0.0.1:${address.port}`);
  store.put("user", "alice", true, Date.now() + 3600_000);
  try {
    const url = createDownloadTicket({ userId: "alice", store, relay, origin }, "/api/alma/documents/current");
    relay.poll("alice", job => {
      assert.ok(job);
      relay.complete("alice", job.id, { status: 200, contentType: "application/pdf", data: Buffer.from("<html>private error</html>").toString("base64") });
    });
    const response = await fetch(url);
    assert.equal(response.status, 502); assert.doesNotMatch(await response.text(), /private error/);
  } finally { relay.close(); server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve())); store.close(); }
});
