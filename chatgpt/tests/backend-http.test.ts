import assert from "node:assert/strict";
import { createServer } from "node:http";
import { after, before, test } from "node:test";
import { buildPortalApiUrl, fetchPortalJson, PortalBackendError } from "../src/backend-http.js";

const backend = createServer((req, res) => {
  if (req.url === "/broken") return void res.end("<html>Private exception</html>");
  if (req.url === "/primitive") return void res.end("null");
  if (req.url?.startsWith("/status/")) {
    res.statusCode = Number(req.url.split("/").at(-1));
    return void res.end("secret password internal host");
  }
  res.setHeader("content-type", "application/json");
  res.end(JSON.stringify({ method: req.method, path: req.url }));
});
const originalBase = process.env.PORTAL_API_BASE_URL;
let baseUrl = "";
before(async () => {
  await new Promise<void>((resolve) => backend.listen(0, "127.0.0.1", resolve));
  const address = backend.address();
  assert.ok(address && typeof address === "object");
  baseUrl = `http://127.0.0.1:${address.port}`;
  process.env.PORTAL_API_BASE_URL = `${baseUrl}/`;
});
after(async () => {
  backend.closeAllConnections();
  await new Promise<void>((resolve) => backend.close(() => resolve()));
  if (originalBase === undefined) delete process.env.PORTAL_API_BASE_URL;
  else process.env.PORTAL_API_BASE_URL = originalBase;
});

test("joins a trailing slash and preserves encoded queries", async () => {
  const result = await fetchPortalJson<{ path: string }>("/api/test?query=Neural%20Data");
  assert.equal(result.path, "/api/test?query=Neural%20Data");
});
test("passes the write method without retrying", async () => {
  assert.equal((await fetchPortalJson<{ method: string }>("/action", { method: "POST" })).method, "POST");
});
for (const status of [401, 403, 429, 500]) {
  test(`reports HTTP ${status} without leaking upstream body`, async () => {
    await assert.rejects(fetchPortalJson(`/status/${status}`), (error: unknown) => {
      assert.ok(error instanceof PortalBackendError);
      assert.doesNotMatch(error.message, /secret|password|127\.0\.0\.1/);
      assert.match(error.message, status === 401 || status === 403 ? /access was denied/ : status === 429 ? /busy/ : /HTTP 500/);
      return true;
    });
  });
}
test("invalid JSON and primitive payloads return useful errors", async () => {
  await assert.rejects(fetchPortalJson("/broken"), /invalid JSON/);
  await assert.rejects(fetchPortalJson("/primitive"), /invalid response/);
});
test("does not allow cross-origin document links", () => {
  assert.throws(() => buildPortalApiUrl("https://attacker.example/private.pdf"), /unsupported download URL/);
  assert.throws(() => buildPortalApiUrl("//attacker.example/private.pdf"), /unsupported download URL/);
});
test("missing and invalid configuration return explicit errors", () => {
  delete process.env.PORTAL_API_BASE_URL;
  assert.throws(() => buildPortalApiUrl("/test"), /not configured/);
  process.env.PORTAL_API_BASE_URL = "ftp://backend.example";
  assert.throws(() => buildPortalApiUrl("/test"), /configuration is invalid/);
  process.env.PORTAL_API_BASE_URL = baseUrl;
});
test("network, timeout and body-read failures remain typed", async () => {
  const originalFetch = globalThis.fetch;
  for (const name of ["TypeError", "TimeoutError", "AbortError"]) {
    let count = 0;
    globalThis.fetch = async (_input, init) => {
      count++;
      assert.ok(init?.signal instanceof AbortSignal);
      const error = new Error("internal secret");
      error.name = name;
      throw error;
    };
    try {
      await assert.rejects(fetchPortalJson("/action", { method: "POST" }), (error: unknown) => {
        assert.ok(error instanceof PortalBackendError);
        assert.match(error.message, name === "TypeError" ? /could not be reached/ : /timed out/);
        assert.doesNotMatch(error.message, /secret/);
        return true;
      });
      assert.equal(count, 1);
    } finally { globalThis.fetch = originalFetch; }
  }
});
