import { connectBridge } from "./widget-bridge.js";

interface HostContext {
  theme?: "light" | "dark";
  displayMode?: "inline" | "fullscreen" | "pip";
  styles?: { variables?: Record<string, string | undefined> };
}

export function connectHostAppearance(onDisplayMode: (expanded: boolean) => void) {
  const apply = (context: HostContext) => {
    if (context.theme) document.documentElement.dataset.theme = context.theme;
    for (const [key, value] of Object.entries(context.styles?.variables ?? {})) {
      if (/^--(?:color-|font-|border-radius-|border-width-|shadow-)/.test(key) && typeof value === "string") {
        document.documentElement.style.setProperty(key, value);
      }
    }
    if (context.displayMode) onDisplayMode(context.displayMode === "fullscreen");
  };
  apply({ theme: window.openai?.theme, displayMode: window.openai?.displayMode });
  window.addEventListener("message", (event) => {
    if (event.source !== window.parent || event.data?.jsonrpc !== "2.0") return;
    if (event.data.method === "ui/notifications/host-context-changed") apply(event.data.params ?? {});
  });
  window.addEventListener("openai:set_globals", (event) => {
    const globals = (event as CustomEvent<{ globals?: HostContext }>).detail?.globals;
    if (globals) apply(globals);
  });
  if (!window.openai?.callTool && window.parent !== window) {
    void connectBridge().then((result) => {
      const context = (result as { hostContext?: HostContext })?.hostContext;
      if (context) apply(context);
    }).catch(() => undefined); // main.ts renders connection errors.
  }
}
