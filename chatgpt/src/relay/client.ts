import { readFile, writeFile, mkdir, unlink } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";
import { maxRelayBytes, maxJsonBytes, validateRelayRequest, type RelayRequest } from "./contract.js";
interface Device { server: string; userId: string; deviceToken: string; credential: string; }
const args = process.argv.slice(2);
const server = new URL(args[args.indexOf("--server") + 1] ?? "");
const backend = new URL(args.includes("--backend") ? args[args.indexOf("--backend") + 1] : "http://127.0.0.1:8000");
if (server.pathname !== "/" || server.username || server.password || server.search || server.hash ||
    (server.protocol !== "https:" && !(server.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(server.hostname)))) throw new Error("--server must be an HTTPS origin or loopback development origin.");
if (backend.protocol !== "http:" || !["127.0.0.1", "[::1]"].includes(backend.hostname) || backend.username || backend.password || backend.pathname !== "/" || backend.search || backend.hash) throw new Error("--backend must be the numeric loopback HTTP origin of your local Python API.");
const directory = join(homedir(), ".tuebingen-study-hub");
const file = join(directory, `${Buffer.from(server.origin).toString("base64url")}.json`);
let device: Device;
try { device = JSON.parse(await readFile(file, "utf8")); }
catch (error) {
  if ((error as NodeJS.ErrnoException).code !== "ENOENT" || args.includes("--disconnect")) throw error;
  const response = await fetch(new URL("/sidecar/register", server), { method: "POST", redirect: "error", signal: AbortSignal.timeout(10_000) });
  if (!response.ok) throw new Error(`Account link creation failed (HTTP ${response.status}).`);
  device = { ...await response.json() as Omit<Device, "server">, server: server.origin };
  await mkdir(directory, { recursive: true, mode: 0o700 });
  await writeFile(file, JSON.stringify(device), { mode: 0o600, flag: "wx" });
}
if (device.server !== server.origin || !/^[A-Za-z0-9_-]{43}$/.test(device.deviceToken)) throw new Error("Stored device connection is invalid.");
const auth = { Authorization: `Bearer ${device.deviceToken}` };
if (args.includes("--disconnect")) {
  const response = await fetch(new URL("/sidecar/connection", server), { method: "DELETE", headers: auth, redirect: "error" });
  if (!response.ok && response.status !== 401) throw new Error("Disconnection failed. Try again.");
  await unlink(file);
  console.log("Account link deleted. OAuth access and device access are invalidated.");
  process.exit(0);
}
console.log(`Connect on ${server.origin}. Enter this link password on its connection page only:\n${device.credential}\nYour university credentials remain in the local Python API.`);

async function handle(request: RelayRequest) {
  let status = 502, contentType = "application/json", bytes = Buffer.from('{"error":"Local university request failed. Check the university portal before retrying an action."}');
  try {
    validateRelayRequest(request);
    const response = await fetch(new URL(request.path, backend), {
      method: request.method, body: request.body, headers: request.contentType ? { "content-type": request.contentType } : {},
      redirect: "error", signal: AbortSignal.timeout(25_000),
    });
    if (response.ok) {
      const limit = request.path === "/api/alma/documents/current" ? maxRelayBytes : maxJsonBytes;
      const reader = response.body?.getReader();
      if (!reader) throw new Error("Empty response.");
      const chunks: Uint8Array[] = [];
      let size = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.length;
        if (size > limit) { await reader.cancel(); throw new Error("Response too large."); }
        chunks.push(value);
      }
      bytes = Buffer.concat(chunks); status = response.status;
      contentType = response.headers.get("content-type") ?? "application/octet-stream";
      if (!contentType.startsWith("application/json") && !contentType.startsWith("application/pdf")) throw new Error("Unsupported response type.");
    } else status = response.status;
  } catch { status = 502; contentType = "application/json"; bytes = Buffer.from('{"error":"Local request result unavailable. Check action status before retrying."}'); }
  const delivered = await fetch(new URL(`/sidecar/result/${encodeURIComponent(request.id)}`, server), {
    method: "POST", headers: { ...auth, "content-type": "application/json" },
    body: JSON.stringify({ status, contentType, data: bytes.toString("base64") }), redirect: "error", signal: AbortSignal.timeout(10_000),
  });
  if (!delivered.ok) console.error(`Result delivery failed (HTTP ${delivered.status}). Check action status; no action was retried.`);
}
const active = new Set<Promise<void>>();
let stopped = false;
process.once("SIGINT", () => { stopped = true; });
process.once("SIGTERM", () => { stopped = true; });
while (!stopped) {
  if (active.size >= 4) await Promise.race(active);
  try {
    const response = await fetch(new URL("/sidecar/next", server), { headers: auth, redirect: "error", signal: AbortSignal.timeout(25_000) });
    if (response.status === 401) throw new Error("Device connection revoked. Remove the local link using --disconnect, then connect again.");
    if (response.status === 204) continue;
    if (!response.ok) throw new Error(`Device poll failed (HTTP ${response.status}).`);
    const job = await response.json() as RelayRequest;
    const work = handle(job).catch(() => console.error("Result delivery unavailable. Check university action status before retrying."));
    active.add(work); void work.finally(() => active.delete(work));
  } catch (error) {
    console.error(error instanceof Error ? error.message : "Device connection failed.");
    if (error instanceof Error && error.message.startsWith("Device connection revoked")) { stopped = true; break; }
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
}
await Promise.allSettled(active);
