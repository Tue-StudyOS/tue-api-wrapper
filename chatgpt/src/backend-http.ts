import { PortalBackendError } from "./backend-error.js";
import { studyContext } from "./request-context.js";
import { createDownloadTicket } from "./downloads.js";
export { PortalBackendError } from "./backend-error.js";

export function buildPortalApiUrl(path: string): string {
  const context = studyContext.getStore();
  if (context) return createDownloadTicket(context, path);
  const baseUrl = process.env.PORTAL_API_BASE_URL;
  if (!baseUrl) {
    throw new PortalBackendError("The study service is not configured. Contact support.");
  }
  let base: URL;
  try { base = new URL(baseUrl); } catch {
    throw new PortalBackendError("The study service configuration is invalid. Contact support.");
  }
  if (!["http:", "https:"].includes(base.protocol) || base.username || base.password) {
    throw new PortalBackendError("The study service configuration is invalid. Contact support.");
  }
  const url = new URL(path, `${base.href.replace(/\/$/, "")}/`);
  if (url.origin !== base.origin) {
    throw new PortalBackendError("The study service returned an unsupported download URL.");
  }
  return url.href;
}

export async function fetchPortalJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  try {
    const context = studyContext.getStore();
    let response: Response;
    if (context) {
      const result = await context.relay.request(context.userId, {
        path, method: init.method === "POST" ? "POST" : "GET",
        body: init.body?.toString(), contentType: new Headers(init.headers).get("content-type") ?? undefined,
      });
      response = new Response(Buffer.from(result.data, "base64"), { status: result.status, headers: { "content-type": result.contentType } });
    } else {
      response = await fetch(buildPortalApiUrl(path), { ...init, signal: AbortSignal.timeout(30_000), redirect: "error" });
    }
    if (!response.ok) {
      const message = response.status === 401 || response.status === 403
        ? "University access was denied. Check your account connection."
        : response.status === 429
          ? "The study service is busy. Try again later."
          : `The study service request failed (HTTP ${response.status}). Try again or contact support.`;
      throw new PortalBackendError(message);
    }
    const data: unknown = await response.json();
    if (data === null || typeof data !== "object") {
      throw new PortalBackendError("The study service returned an invalid response. Contact support.");
    }
    return data as T;
  } catch (error) {
    if (error instanceof PortalBackendError) throw error;
    if (error instanceof Error && ["TimeoutError", "AbortError"].includes(error.name)) {
      throw new PortalBackendError("The study service timed out. Check its status before retrying an action.");
    }
    if (error instanceof SyntaxError) {
      throw new PortalBackendError("The study service returned invalid JSON. Contact support.");
    }
    throw new PortalBackendError("The study service could not be reached. Check its status and try again.");
  }
}
