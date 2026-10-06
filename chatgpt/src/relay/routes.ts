import { Router, json } from "express";
import { rateLimit } from "express-rate-limit";
import { randomUUID } from "node:crypto";
import { StateStore, digest, secret } from "../auth/state-store.js";
import type { SidecarRelay } from "./relay.js";
import { maxRelayBytes } from "./contract.js";
const permanent = 253402300799000;

export function sidecarRoutes(store: StateStore, relay: SidecarRelay) {
  const router = Router();
  router.post("/register", rateLimit({ windowMs: 3600_000, limit: 5 }), json({ limit: "1kb" }), (_req, res) => {
    const userId = randomUUID(), deviceToken = secret(), credential = secret();
    store.put("user", userId, true, permanent);
    store.put("device", digest(deviceToken), { userId, loginHash: digest(credential) }, permanent);
    store.put("login-secret", digest(credential), { userId }, permanent);
    res.status(201).json({ userId, deviceToken, credential });
  });
  router.use((req, res, next) => {
    const token = req.headers.authorization?.match(/^Bearer ([A-Za-z0-9_-]{43})$/)?.[1];
    const device = token && store.get<{ userId: string; loginHash: string }>("device", digest(token));
    if (!device) { res.status(401).json({ error: "Device connection expired. Link again." }); return; }
    res.locals.device = device;
    res.locals.tokenHash = digest(token!);
    next();
  });
  router.get("/next", (req, res) => {
    try {
      const cancel = relay.poll(res.locals.device.userId, job => {
        if (!res.writableEnded) job ? res.json(job) : res.status(204).end();
      });
      res.on("close", cancel);
    } catch { res.status(409).json({ error: "A device poll is already active." }); }
  });
  router.post("/result/:id", json({ limit: "12mb" }), (req, res) => {
    const data = req.body;
    if (!data || typeof data.data !== "string" || data.data.length > Math.ceil(maxRelayBytes / 3) * 4 ||
        !/^[A-Za-z0-9+/]*={0,2}$/.test(data.data) || !Number.isInteger(data.status) || data.status < 200 || data.status > 599 ||
        typeof data.contentType !== "string" || data.contentType.length > 128) {
      res.status(400).json({ error: "Invalid device response." }); return;
    }
    const accepted = relay.complete(res.locals.device.userId, String(req.params.id), data);
    res.status(accepted ? 204 : 404).end();
  });
  router.delete("/connection", (_req, res) => {
    relay.disconnect(res.locals.device.userId);
    store.delete("user", res.locals.device.userId);
    store.delete("login-secret", res.locals.device.loginHash);
    store.delete("device", res.locals.tokenHash);
    res.status(204).end();
  });
  return router;
}
