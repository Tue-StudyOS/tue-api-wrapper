import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { loadDashboard, loadDocumentsSummary } from "../backend.js";
import { readOnlyAnnotations, runWidgetTool } from "../tool-runtime.js";
import { widgetUri } from "../widget-resources.js";

export function registerWidgetTools(server: McpServer) {
  registerAppTool(
    server,
    "show_dashboard",
    {
      outputSchema: outputSchemas.show_dashboard,
      title: "Show study dashboard",
      description:
        "Use this when the user wants a compact overview of upcoming events, documents, exams, and ILIAS entry points.",
      inputSchema: {
        term: z.string().min(1).optional(),
      },
      annotations: readOnlyAnnotations(),
      _meta: {
        ui: {
          resourceUri: widgetUri,
        },
        "openai/outputTemplate": widgetUri,
        "openai/toolInvocation/invoking": "Building dashboard…",
        "openai/toolInvocation/invoked": "Dashboard ready",
      },
    },
    async ({ term }) =>
      runWidgetTool(async () => {
        const dashboard = await loadDashboard(term);
        return {
          structuredContent: {
            view: "dashboard",
            dashboard,
          },
          content: [
            {
              type: "text" as const,
              text: `Showing the unified study dashboard for ${dashboard.termLabel}.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "list_documents",
    {
      outputSchema: outputSchemas.list_documents,
      title: "Show study-service documents",
      description:
        "Use this when the user specifically wants Alma study-service document jobs or certificate options in the widget.",
      inputSchema: {},
      annotations: readOnlyAnnotations(),
      _meta: {
        ui: {
          resourceUri: widgetUri,
        },
        "openai/outputTemplate": widgetUri,
        "openai/toolInvocation/invoking": "Loading documents…",
        "openai/toolInvocation/invoked": "Documents ready",
      },
    },
    async () =>
      runWidgetTool(async () => {
        const documents = await loadDocumentsSummary();
        const availableCount =
          documents.reports.length +
          documents.outputRequests.length +
          (documents.currentDownloadAvailable ? 1 : 0);
        return {
          structuredContent: {
            view: "documents",
            documents,
          },
          content: [
            {
              type: "text" as const,
              text: availableCount
                ? `Loaded ${documents.reports.length} Alma study-service document jobs, ${documents.outputRequests.length} output-request groups, and ${documents.currentDownloadAvailable ? "a current PDF download" : "no current PDF download"}.`
                : "The Alma study-service page loaded, but no report jobs, output-request groups, or current PDF downloads are currently available.",
            },
          ],
        };
      }),
  );
}
