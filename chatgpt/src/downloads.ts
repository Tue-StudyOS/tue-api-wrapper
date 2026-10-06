import type { StudyContext } from "./request-context.js";
import { StateStore, digest, secret } from "./auth/state-store.js";
import type { SidecarRelay } from "./relay/relay.js";
import { Router } from "express";
import { PortalBackendError } from "./backend-error.js";
interface Ticket { userId: string; path: string; }
export function createDownloadTicket(context: StudyContext, path: string) {
  // Private download links are capabilities: short-lived, single-use, and never logged.
  if (path !== "/api/alma/documents/current") {
    throw new PortalBackendError("The study service returned an unsupported document URL.");
  }
  const token = secret();
  context.store.put("download", digest(token), { userId: context.userId, path }, Date.now() + 120_000);
  return new URL(`/downloads/${token}`, context.origin).href;
}
export function downloadRoutes(store: StateStore, relay: SidecarRelay) {
  const router = Router();
  router.get("/:token", async (req, res) => {
    const ticket = store.take<Ticket>("download", digest(String(req.params.token)));
    if (!ticket || !store.get("user", ticket.userId)) { res.status(410).send("Document link expired. Request a new link."); return; }
    try {
      const response = await relay.request(ticket.userId, { path: ticket.path, method: "GET" });
      const bytes = Buffer.from(response.data, "base64");
      if (response.status !== 200 || !response.contentType.startsWith("application/pdf") || !bytes.subarray(0, 5).equals(Buffer.from("%PDF-"))) {
        res.status(502).send("The device did not return a PDF. Check the university portal."); return;
      }
      res.set({ "Content-Type": "application/pdf", "Content-Disposition": 'attachment; filename="study-document.pdf"', "Cache-Control": "no-store", "Referrer-Policy": "no-referrer" }).send(bytes);
    } catch { res.status(503).send("Device disconnected. Start your sidecar and request a new link."); }
  });
  return router;
}
