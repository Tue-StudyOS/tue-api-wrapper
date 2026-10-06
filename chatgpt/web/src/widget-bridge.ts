interface ToolResult<T = unknown> {
  structuredContent?: T;
  content?: Array<{ type: string; text?: string }>;
  _meta?: Record<string, unknown>;
  isError?: boolean;
}

type PendingRequest = { resolve: (value: unknown) => void; reject: (error: Error) => void; timer: ReturnType<typeof setTimeout> };
const pending = new Map<string, PendingRequest>();
let sequence = 0;
let connection: Promise<unknown> | undefined;
let latestMetadata: Record<string, unknown> | undefined;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object";
}

window.addEventListener("message", (event) => {
  if (event.source !== window.parent || !isRecord(event.data) || event.data.jsonrpc !== "2.0") return;
  const message = event.data;
  if (message.method === "ui/notifications/tool-result" && isRecord(message.params)) {
    latestMetadata = isRecord(message.params._meta) ? message.params._meta : undefined;
  }
  const request = typeof message.id === "string" ? pending.get(message.id) : undefined;
  if (!request) return;
  pending.delete(message.id as string);
  clearTimeout(request.timer);
  if (isRecord(message.error)) request.reject(new Error(String(message.error.message ?? "The host request failed.")));
  else request.resolve(message.result);
});

function request(method: string, params: unknown): Promise<unknown> {
  if (window.parent === window) return Promise.reject(new Error("Open this view inside ChatGPT or an MCP Apps host."));
  const id = `study-hub-${++sequence}`;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error("The host did not respond. Check the connection before retrying an action."));
    }, 35_000);
    pending.set(id, { resolve, reject, timer });
    window.parent.postMessage({ jsonrpc: "2.0", id, method, params }, "*");
  });
}

export function connectBridge(): Promise<unknown> {
  connection ??= request("ui/initialize", {
    protocolVersion: "2026-01-26",
    appInfo: { name: "tue-study-hub", version: "0.8.0" },
    appCapabilities: { availableDisplayModes: ["inline", "fullscreen"] },
  }).then((result) => {
    window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} }, "*");
    return result;
  });
  return connection;
}

export function readToolMetadata(): Record<string, unknown> | undefined {
  return latestMetadata ?? window.openai?.toolResponseMetadata;
}

export function requireToolContent<T>(response: ToolResult<T>): T {
  const payload = response.structuredContent;
  const message = isRecord(payload) && typeof payload.error === "string" ? payload.error
    : isRecord(payload) && payload.view === "error" && typeof payload.message === "string" ? payload.message
    : undefined;
  if (response.isError || message) {
    throw new Error(message ?? response.content?.find((item) => item.type === "text")?.text ?? "The tool request failed.");
  }
  if (payload === undefined || payload === null) throw new Error("The tool returned no data. Try again or contact support.");
  return payload;
}

export async function callHostTool<T>(name: string, args: Record<string, unknown> = {}): Promise<T> {
  let response: ToolResult<T>;
  if (window.openai?.callTool) {
    response = await window.openai.callTool<T>(name, args);
  } else {
    await connectBridge();
    response = await request("tools/call", { name, arguments: args }) as ToolResult<T>;
  }
  return requireToolContent(response);
}

export async function sendFollowUp(prompt: string): Promise<void> {
  if (window.openai?.sendFollowUpMessage) {
    await window.openai.sendFollowUpMessage({ prompt });
    return;
  }
  await connectBridge();
  await request("ui/message", { role: "user", content: [{ type: "text", text: prompt }] });
}

export async function requestDisplayMode(mode: "inline" | "fullscreen"): Promise<string> {
  if (window.openai?.requestDisplayMode) {
    const result = await window.openai.requestDisplayMode({ mode });
    return result?.mode ?? window.openai.displayMode ?? mode;
  }
  await connectBridge();
  const result = await request("ui/request-display-mode", { mode }) as { mode?: string };
  if (!result?.mode) throw new Error("The host did not confirm the display mode.");
  return result.mode;
}
