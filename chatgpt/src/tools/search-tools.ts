import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { fetchItem, searchItems } from "../backend.js";
import { readOnlyAnnotations, runReadTool } from "../tool-runtime.js";

export function registerSearchTools(server: McpServer) {
  registerAppTool(
    server,
    "search",
    {
      outputSchema: outputSchemas.search,
      title: "Search unified study portal",
      description:
        "Use this when the user wants to search Alma and ILIAS items by topic, course name, or document label.",
      inputSchema: {
        query: z.string().min(1),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ query }) =>
      runReadTool(async () => {
        const results = await searchItems(query);
        return {
          structuredContent: {
            results,
          },
          content: [
            {
              type: "text" as const,
              text: JSON.stringify({ results: results.map(({ id, title, url }) => ({ id, title, url })) }),
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "fetch",
    {
      outputSchema: outputSchemas.fetch,
      title: "Fetch unified study item",
      description:
        "Use this when the user already has an item id from search and wants the full text for that Alma or ILIAS result.",
      inputSchema: {
        id: z.string().min(1),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ id }) =>
      runReadTool(async () => {
        const item = await fetchItem(id);
        return {
          structuredContent: {
            item,
          },
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(item),
            },
          ],
        };
      }),
  );
}
