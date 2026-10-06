/** Isolated synthetic protocol benchmark. Never connects to university services. */
import { createServer } from "node:http";
import { randomUUID } from "node:crypto";
import { StateStore, digest, secret } from "../src/auth/state-store.js";
import { createStudyHttpApp } from "../src/http-app.js";
import { SidecarRelay } from "../src/relay/relay.js";

const server = createServer(), store = new StateStore(":memory:"), relay = new SidecarRelay();
await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
const address = server.address();
if (!address || typeof address !== "object") throw new Error("Loopback server did not start.");
const origin = `http://127.0.0.1:${address.port}`;
server.on("request", createStudyHttpApp(new URL(origin), store, relay).app);
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const percentile = (values: number[], p: number) => +values.sort((a, b) => a - b)[Math.max(0, Math.ceil(values.length * p) - 1)].toFixed(2);
const results = [];
let active = true;
const connected = new Set<string>();
function connectDevice(userId: string) {
  relay.poll(userId, job => {
    if (!active || !connected.has(userId)) return;
    if (job) {
      setTimeout(() => relay.complete(userId, job.id, {
        status: 200, contentType: "application/json",
        data: Buffer.from(JSON.stringify([{ title: "Synthetic benchmark task", userId }])).toString("base64"),
      }), 10);
    }
    connectDevice(userId);
  });
}
try {
  if ((await fetch(`${origin}/mcp`, { method: "POST" })).status !== 401) throw new Error("Unauthenticated control failed.");
  for (const readers of [30, 60]) {
    const rows: number[] = [];
    let errors = 0, maxRss = 0, maxHeap = 0;
    const accounts = Array.from({ length: readers }, () => ({ userId: randomUUID(), token: secret(), group: randomUUID() }));
    for (const account of accounts) {
      const expiry = Date.now() + 300_000;
      store.put("user", account.userId, true, expiry);
      store.put("group", account.group, true, expiry);
      store.put("access", digest(account.token), { userId: account.userId, group: account.group, clientId: "synthetic-benchmark", scopes: ["study"], resource: `${origin}/mcp`, expiresAt: Math.floor(expiry / 1000) }, expiry);
      connected.add(account.userId);
      connectDevice(account.userId);
    }
    const start = performance.now(), cpuStart = process.cpuUsage();
    const stop = start + 15_000;
    await Promise.all(accounts.map(async (account, index) => {
      await sleep(index / readers * 2000);
      let count = 0;
      while (performance.now() < stop) {
        const began = performance.now();
        const profile = count++ % 2 === 0;
        try {
          const response = await fetch(`${origin}/mcp`, {
            method: "POST", headers: { Authorization: `Bearer ${account.token}`, "content-type": "application/json", Accept: "application/json, text/event-stream" },
            body: JSON.stringify({ jsonrpc: "2.0", id: count, method: "tools/call", params: { name: profile ? "get_connection_profile" : "get_current_tasks", arguments: {} } }), signal: AbortSignal.timeout(5000),
          });
          const payload = await response.json();
          const identity = profile ? payload.result?.structuredContent?.id : payload.result?.structuredContent?.tasks?.[0]?.userId;
          if (response.status !== 200 || payload.result?.isError || identity !== account.userId) errors++;
        } catch { errors++; }
        rows.push(performance.now() - began);
        const memory = process.memoryUsage(); maxRss = Math.max(maxRss, memory.rss); maxHeap = Math.max(maxHeap, memory.heapUsed);
        await sleep(2000);
      }
    }));
    const elapsed = (performance.now() - start) / 1000;
    const cpu = process.cpuUsage(cpuStart);
    results.push({ readers, requests: rows.length, seconds: +elapsed.toFixed(2), requestsPerSecond: +(rows.length / elapsed).toFixed(2), p50Ms: percentile(rows, .5), p95Ms: percentile(rows, .95), p99Ms: percentile(rows, .99), errors, maxSampledRssMiB: +(maxRss / 1048576).toFixed(2), maxSampledHeapMiB: +(maxHeap / 1048576).toFixed(2), averageOneCoreCpuPercent: +((cpu.user + cpu.system) / (elapsed * 1e6) * 100).toFixed(2) });
    for (const account of accounts) { connected.delete(account.userId); relay.disconnect(account.userId); }
  }
  console.log(JSON.stringify({ synthetic: true, universityCalls: 0, scope: "authenticated MCP profiles and owner-checked relay task reads; 10 ms synthetic device delay; two-second think time; server and load generator share one process", node: process.version, results }, null, 2));
  if (results.some(result => result.errors)) process.exitCode = 1;
} finally {
  active = false; relay.close(); server.closeAllConnections();
  await new Promise<void>(resolve => server.close(() => resolve())); store.close();
}
