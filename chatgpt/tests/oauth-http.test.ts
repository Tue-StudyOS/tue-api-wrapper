import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { createServer } from "node:http";
import { createHash } from "node:crypto";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { createStudyHttpApp } from "../src/http-app.js";
import { StateStore } from "../src/auth/state-store.js";
import { SidecarRelay } from "../src/relay/relay.js";

const server = createServer(), store = new StateStore(":memory:"), relay = new SidecarRelay();
let origin = "";
let clientId = "";
let alice: { userId: string; deviceToken: string; credential: string };
const verifier = "a".repeat(64), redirect = "https://chatgpt.com/connector/oauth/test";
const challenge = createHash("sha256").update(verifier).digest("base64url");
const form = (data: Record<string, string>) => ({ method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: new URLSearchParams(data) });
async function grant(credential = alice.credential) {
  const params = new URLSearchParams({ client_id: clientId, redirect_uri: redirect, response_type: "code", code_challenge: challenge, code_challenge_method: "S256", scope: "study", resource: `${origin}/mcp`, state: "roundtrip-state" });
  const page = await fetch(`${origin}/authorize?${params}`, { redirect: "manual" });
  assert.equal(page.status, 200);
  const cookie = page.headers.get("set-cookie")!.split(";")[0];
  const nonce = (await page.text()).match(/name="nonce" value="([A-Za-z0-9_-]+)"/)![1];
  const response = await fetch(`${origin}/connect`, {
    ...form({ nonce, credential }), headers: { "content-type": "application/x-www-form-urlencoded", cookie, Origin: origin }, redirect: "manual",
  });
  assert.equal(response.status, 303);
  const location = new URL(response.headers.get("location")!);
  assert.equal(location.searchParams.get("state"), "roundtrip-state");
  return location.searchParams.get("code")!;
}
async function exchange(code: string, codeVerifier = verifier) {
  return fetch(`${origin}/token`, form({ grant_type: "authorization_code", client_id: clientId, code, code_verifier: codeVerifier, redirect_uri: redirect, resource: `${origin}/mcp` }));
}
before(async () => {
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address(); assert.ok(address && typeof address === "object");
  origin = `http://127.0.0.1:${address.port}`;
  server.on("request", createStudyHttpApp(new URL(origin), store, relay).app);
  const registration = await fetch(`${origin}/register`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ client_name: "Release test client", redirect_uris: [redirect], token_endpoint_auth_method: "none", grant_types: ["authorization_code", "refresh_token"], response_types: ["code"] }) });
  assert.equal(registration.status, 201);
  clientId = (await registration.json() as { client_id: string }).client_id;
  alice = await (await fetch(`${origin}/sidecar/register`, { method: "POST" })).json();
});
after(async () => {
  relay.close(); server.closeAllConnections();
  await new Promise<void>(resolve => server.close(() => resolve())); store.close();
});

test("MCP rejects unauthenticated requests and advertises the resource and issuer", async () => {
  const response = await fetch(`${origin}/mcp`, { method: "POST" });
  assert.equal(response.status, 401);
  assert.match(response.headers.get("www-authenticate")!, /resource_metadata=/);
  const metadata = await (await fetch(`${origin}/.well-known/oauth-protected-resource/mcp`)).json();
  assert.equal(metadata.resource, `${origin}/mcp`);
  assert.deepEqual(metadata.authorization_servers, [new URL(origin).href]);
  const authorization = await (await fetch(`${origin}/.well-known/oauth-authorization-server`)).json();
  assert.deepEqual(authorization.code_challenge_methods_supported, ["S256"]);
});
test("connection form rejects cross-origin and missing-cookie requests", async () => {
  const response = await fetch(`${origin}/connect`, { ...form({ nonce: "forged", credential: alice.credential }), headers: { "content-type": "application/x-www-form-urlencoded", Origin: "https://attacker.invalid" } });
  assert.equal(response.status, 400);
});
test("OAuth rejects another resource and unregistered redirect URIs", async () => {
  const params = new URLSearchParams({ client_id: clientId, redirect_uri: redirect, response_type: "code", code_challenge: challenge, code_challenge_method: "S256", resource: "https://other.invalid/mcp" });
  const response = await fetch(`${origin}/authorize?${params}`, { redirect: "manual" });
  assert.equal(new URL(response.headers.get("location")!).searchParams.get("error"), "invalid_target");
  params.set("redirect_uri", "https://attacker.invalid");
  assert.equal((await fetch(`${origin}/authorize?${params}`, { redirect: "manual" })).status, 400);
});
test("PKCE is required, codes cannot replay, and MCP exposes an opaque stable profile", async () => {
  const code = await grant();
  assert.equal((await exchange(code, "b".repeat(64))).status, 400);
  const response = await exchange(code); assert.equal(response.status, 200);
  const token = await response.json();
  assert.equal((await exchange(code)).status, 400);
  const client = new Client({ name: "release-http-tests", version: "1" });
  try {
    await client.connect(new StreamableHTTPClientTransport(new URL(`${origin}/mcp`), { requestInit: { headers: { Authorization: `Bearer ${token.access_token}` } } }));
    const profile = await client.callTool({ name: "get_connection_profile", arguments: {} });
    assert.deepEqual(profile.structuredContent, { id: alice.userId });
    assert.deepEqual(JSON.parse((profile.content as Array<{ text: string }>)[0].text), { id: alice.userId });
    const tools = await client.listTools();
    for (const tool of tools.tools) {
      assert.deepEqual(tool._meta?.securitySchemes, [{ type: "oauth2", scopes: ["study"] }]);
    }
    // The SDK client strips non-MCP top-level extensions; inspect the wire JSON.
    const wire = await fetch(`${origin}/mcp`, { method: "POST", headers: { Authorization: `Bearer ${token.access_token}`, "content-type": "application/json", Accept: "application/json, text/event-stream" }, body: JSON.stringify({ jsonrpc: "2.0", id: 99, method: "tools/list", params: {} }) });
    assert.equal(wire.status, 200);
    const descriptors = await wire.json();
    for (const tool of descriptors.result.tools) assert.deepEqual(tool.securitySchemes, [{ type: "oauth2", scopes: ["study"] }]);
    const result = await client.callTool({ name: "get_current_tasks", arguments: {} });
    assert.equal(result.isError, true);
    assert.match(JSON.stringify(result), /sidecar is disconnected/);
  } finally { await client.close(); }
});
test("refresh rotates, rejects escalation, and revocation invalidates the full grant", async () => {
  const token = await (await exchange(await grant())).json();
  const refresh = (value: string, scope = "study") => fetch(`${origin}/token`, form({ grant_type: "refresh_token", client_id: clientId, refresh_token: value, resource: `${origin}/mcp`, scope }));
  assert.equal((await refresh(token.refresh_token, "admin")).status, 400);
  const response = await refresh(token.refresh_token); assert.equal(response.status, 200);
  const rotated = await response.json();
  assert.equal((await refresh(token.refresh_token)).status, 400);
  assert.equal((await fetch(`${origin}/revoke`, form({ client_id: clientId, token: rotated.refresh_token }))).status, 200);
  for (const access of [token.access_token, rotated.access_token]) {
    assert.equal((await fetch(`${origin}/mcp`, { headers: { Authorization: `Bearer ${access}` } })).status, 401);
  }
  assert.equal((await refresh(rotated.refresh_token)).status, 400);
});
test("deleting the local account link invalidates active OAuth and device access", async () => {
  const token = await (await exchange(await grant())).json();
  const headers = { Authorization: `Bearer ${alice.deviceToken}` };
  assert.equal((await fetch(`${origin}/sidecar/connection`, { method: "DELETE", headers })).status, 204);
  assert.equal((await fetch(`${origin}/sidecar/next`, { headers })).status, 401);
  assert.equal((await fetch(`${origin}/mcp`, { headers: { Authorization: `Bearer ${token.access_token}` } })).status, 401);
});
