import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  RESOURCE_MIME_TYPE,
  registerAppResource,
} from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, "..");
const widgetJs = readFileSync(join(projectRoot, "web/dist/widget.js"), "utf8");
const widgetCss = readFileSync(join(projectRoot, "web/dist/widget.css"), "utf8");

const widgetDomain = process.env.APP_BASE_URL;

export const widgetUri = "ui://study-hub/dashboard-v9.html";
export const detailWidgetUri = "ui://study-hub/detail-v9.html";
export const actionWidgetUri = "ui://study-hub/action-v9.html";
export const mensaWidgetUri = "ui://study-hub/mensa-v9.html";

const widgetAliases = {
  dashboard: [
    widgetUri,
    "ui://study-hub/dashboard-v8.html",
    "ui://study-hub/dashboard-v7.html",
    "ui://study-hub/dashboard-v6.html",
    "ui://study-hub/dashboard-v5.html",
    "ui://study-hub/dashboard-v4.html",
  ],
  detail: [
    detailWidgetUri,
    "ui://study-hub/detail-v8.html",
    "ui://study-hub/detail-v7.html",
    "ui://study-hub/detail-v6.html",
    "ui://study-hub/detail-v5.html",
    "ui://study-hub/detail-v4.html",
  ],
  action: [
    actionWidgetUri,
    "ui://study-hub/action-v8.html",
    "ui://study-hub/action-v7.html",
    "ui://study-hub/action-v6.html",
    "ui://study-hub/action-v5.html",
    "ui://study-hub/action-v4.html",
  ],
  mensa: [
    mensaWidgetUri,
    "ui://study-hub/mensa-v8.html",
  ],
} as const;

type WidgetTemplate = "dashboard" | "detail" | "action" | "mensa";

function buildWidgetHtml(template: WidgetTemplate, uri: string) {
  const meta: Record<string, unknown> = {
    "openai/ui": { availableDisplayModes: ["inline", "fullscreen"] },
    ui: {
      prefersBorder: true,
      csp: {
        connectDomains: [],
        resourceDomains: template === "mensa" ? ["https://www.my-stuwe.de"] : [],
      },
    },
    "openai/widgetDescription":
      template === "detail"
        ? "Shows a host modal with focused details for a selected study item."
        : template === "action"
          ? "Shows a human confirmation screen for a prepared critical university action with Proceed and Cancel controls."
          : template === "mensa"
            ? "Shows Tübingen mensa menus with canteen filters, prices, diet tags, and source links."
            : "Shows an interactive study dashboard with upcoming Alma events, open ILIAS tasks, exam progress, documents, and learning spaces.",
  };

  if (widgetDomain) {
    meta.ui = {
      ...(meta.ui as Record<string, unknown>),
      domain: widgetDomain,
    };
  }

  return {
    contents: [
      {
        uri,
        mimeType: RESOURCE_MIME_TYPE,
        text: `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>${widgetCss}</style>
  </head>
  <body data-template="${template}">
    <div id="root"></div>
    <script type="module">${widgetJs}</script>
  </body>
</html>`,
        _meta: meta,
      },
    ],
  };
}

export function registerWidgetResources(server: McpServer) {
  for (const [template, uris] of Object.entries(widgetAliases)) {
    uris.forEach((uri, index) => {
      registerAppResource(
        server,
        `study-hub-${template}-widget-${index}`,
        uri,
        {},
        async () => buildWidgetHtml(template as WidgetTemplate, uri),
      );
    });
  }
}
