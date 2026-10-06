type WidgetRenderer = (result: unknown) => void;

interface HostGlobals {
  toolOutput?: unknown;
  toolResponseMetadata?: Record<string, unknown>;
}

interface ToolResultNotification {
  structuredContent?: unknown;
  _meta?: Record<string, unknown>;
}

interface JsonRpcNotification {
  jsonrpc?: string;
  method?: string;
  params?: ToolResultNotification;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object");
}

function hasView(value: unknown): boolean {
  return isRecord(value) && typeof value.view === "string";
}

function dashboardFromMetadata(metadata: Record<string, unknown> | undefined): unknown {
  if (!isRecord(metadata?.dashboard)) {
    return null;
  }
  return {
    view: "dashboard",
    dashboard: metadata.dashboard
  };
}

function errorFromToolOutput(toolOutput: unknown): unknown {
  if (!isRecord(toolOutput) || typeof toolOutput.error !== "string") {
    return null;
  }
  return {
    view: "error",
    message: toolOutput.error
  };
}

function normalizeToolResult(toolOutput: unknown, metadata?: Record<string, unknown>): unknown {
  if (hasView(toolOutput)) {
    return toolOutput;
  }
  if (typeof metadata?.error === "string") return { view: "error", message: metadata.error };
  return errorFromToolOutput(toolOutput) ?? dashboardFromMetadata(metadata) ?? toolOutput ?? null;
}

function readOpenAiGlobals(): HostGlobals {
  const hostWindow = window as typeof window & { openai?: HostGlobals };
  return {
    toolOutput: hostWindow.openai?.toolOutput,
    toolResponseMetadata: hostWindow.openai?.toolResponseMetadata
  };
}

export function readInitialWidgetResult(): unknown {
  const globals = readOpenAiGlobals();
  return normalizeToolResult(globals.toolOutput, globals.toolResponseMetadata);
}

export function connectWidgetResultUpdates(render: WidgetRenderer) {
  window.addEventListener(
    "message",
    (event) => {
      if (event.source !== window.parent) {
        return;
      }

      const message = event.data as JsonRpcNotification;
      if (!message || message.jsonrpc !== "2.0" || message.method !== "ui/notifications/tool-result") {
        return;
      }

      render(normalizeToolResult(message.params?.structuredContent, message.params?._meta));
    },
    { passive: true }
  );

  window.addEventListener(
    "openai:set_globals",
    (event) => {
      const customEvent = event as CustomEvent<{ globals?: HostGlobals }>;
      const globals = customEvent.detail?.globals ?? readOpenAiGlobals();
      if (globals && !("toolOutput" in globals) && !("toolResponseMetadata" in globals)) {
        return;
      }
      render(normalizeToolResult(globals.toolOutput, globals.toolResponseMetadata));
    },
    { passive: true }
  );
}
