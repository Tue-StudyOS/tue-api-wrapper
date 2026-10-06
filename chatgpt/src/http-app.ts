import express from "express";
import { rateLimit } from "express-rate-limit";
import { mcpAuthRouter, getOAuthProtectedResourceMetadataUrl } from "@modelcontextprotocol/sdk/server/auth/router.js";
import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { StateStore } from "./auth/state-store.js";
import { StudyOAuthProvider } from "./auth/provider.js";
import { SidecarRelay } from "./relay/relay.js";
import { sidecarRoutes } from "./relay/routes.js";
import { downloadRoutes } from "./downloads.js";
import { createAppServer, serverName } from "./study-server.js";
import { studyContext } from "./request-context.js";
import { publicPage } from "./public-pages.js";
import { publicStyles } from "./public-styles.js";

export function createStudyHttpApp(origin: URL, store: StateStore, relay = new SidecarRelay()) {
  const app = express();
  app.disable("x-powered-by");
  app.set("trust proxy", "loopback");
  const provider = new StudyOAuthProvider(store, origin);
  app.use((_req, res, next) => {
    res.set({ "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
      "Content-Security-Policy": "default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'" });
    next();
  });
  app.get(["/", "/privacy", "/support", "/terms"], (req, res) => res.type("html").send(publicPage(req.path)));
  app.get("/pages.css", (_req, res) => res.type("css").send(publicStyles));
  app.get("/healthz", (_req, res) => res.json({ status: "ok", service: serverName, mcpPath: "/mcp" }));
  app.use("/sidecar", sidecarRoutes(store, relay));
  app.use("/downloads", rateLimit({ windowMs: 60_000, limit: 30 }), downloadRoutes(store, relay));
  app.post("/connect", rateLimit({ windowMs: 15 * 60_000, limit: 30 }), express.urlencoded({ extended: false, limit: "2kb" }), (req, res) => {
    const cookie = req.headers.cookie?.split(";").map(value => value.trim()).find(value => value.startsWith("study_login="))?.slice(12);
    const nonce = req.body?.nonce, credential = req.body?.credential;
    if (req.headers.origin !== origin.origin || typeof nonce !== "string" || nonce !== cookie || typeof credential !== "string") {
      res.status(400).send("Connection request invalid. Start the account connection again."); return;
    }
    res.clearCookie("study_login", { path: "/" });
    try { res.redirect(303, provider.completeLogin(nonce, credential)); }
    catch { res.status(400).send("Link password invalid or connection expired. Start again."); }
  });
  app.use(mcpAuthRouter({ provider, issuerUrl: origin, resourceServerUrl: provider.resource, scopesSupported: ["study"], resourceName: "Tübingen Study Hub" }));
  app.options("/mcp", (_req, res) => res.set({ "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS", "Access-Control-Allow-Headers": "content-type, authorization, mcp-protocol-version, mcp-session-id" }).status(204).end());
  app.use("/mcp", (_req, res, next) => { res.setHeader("Access-Control-Allow-Origin", "*"); next(); },
    requireBearerAuth({ verifier: provider, requiredScopes: ["study"], resourceMetadataUrl: getOAuthProtectedResourceMetadataUrl(provider.resource) }),
    express.json({ limit: "256kb" }), async (req, res) => {
      if (!["GET", "POST", "DELETE"].includes(req.method)) { res.status(405).end(); return; }
      const userId = req.auth?.extra?.userId;
      if (typeof userId !== "string") { res.status(401).end(); return; }
      await studyContext.run({ userId, store, relay, origin }, async () => {
        const server = createAppServer();
        const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true });
        res.on("close", () => { void transport.close(); void server.close(); });
        try { await server.connect(transport); await transport.handleRequest(req, res, req.body); }
        catch { if (!res.headersSent) res.status(500).json({ error: "Study request could not be completed." }); }
      });
    });
  app.use((_req, res) => res.status(404).json({ error: "Not found." }));
  app.use((error: { status?: number }, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    if (!res.headersSent) res.status(error.status === 413 ? 413 : 400).json({ error: "Request could not be processed." });
  });
  return { app, provider, relay };
}
