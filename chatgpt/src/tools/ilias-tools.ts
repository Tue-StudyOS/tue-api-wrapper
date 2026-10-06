import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import {
  inspectLearningSpace,
  searchLearningSpaces,
} from "../backend.js";
import { asStructured, readOnlyAnnotations, runReadTool } from "../tool-runtime.js";

export function registerIliasTools(server: McpServer) {
  registerAppTool(
    server,
    "search_learning_spaces",
    {
      outputSchema: outputSchemas.search_learning_spaces,
      title: "Search ILIAS learning spaces",
      description:
        "Use this when the user wants to search authenticated ILIAS content beyond current memberships, optionally with advanced filters like content type or creation date.",
      inputSchema: {
        term: z.string().min(1),
        page: z.number().int().min(1).max(20).optional(),
        searchMode: z.string().optional(),
        contentType: z.array(z.string().min(1)).max(10).optional(),
        createdEnabled: z.boolean().optional(),
        createdMode: z.string().optional(),
        createdDate: z.string().optional(),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ term, page, searchMode, contentType, createdEnabled, createdMode, createdDate }) =>
      runReadTool(async () => {
        const results = await searchLearningSpaces({
          term,
          page,
          searchMode,
          contentType,
          createdEnabled,
          createdMode,
          createdDate,
        });
        return {
          structuredContent: asStructured(results),
          content: [
            {
              type: "text" as const,
              text: `Loaded ${results.results.length} ILIAS search results for "${results.query}" on page ${results.page_number}.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "inspect_learning_space",
    {
      outputSchema: outputSchemas.inspect_learning_space,
      title: "Inspect ILIAS learning space",
      description:
        "Use this when the user wants the contents, forum topics, and exercise assignments for a specific ILIAS target URL or goto reference.",
      inputSchema: {
        target: z.string().min(1),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ target }) =>
      runReadTool(async () => {
        const inspection = await inspectLearningSpace(target);
        const sectionCount = inspection.content?.sections.length ?? 0;
        return {
          structuredContent: asStructured(inspection),
          content: [
            {
              type: "text" as const,
              text: `Loaded learning space details with ${sectionCount} content sections, ${inspection.forum.length} forum topics, and ${inspection.exercise.length} exercise assignments.`,
            },
          ],
        };
      }),
  );
}
