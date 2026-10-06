import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import {
  loadCourseCatalogFilters,
  loadCourseDetail,
  loadStudyPlanner,
  searchCourseCatalog,
  searchCourseOfferings,
} from "../backend.js";
import { PortalBackendError } from "../backend-http.js";
import { loadUnifiedCourseDetail } from "../course-detail-backend.js";
import {
  asStructured,
  courseFilterListSchema,
  readOnlyAnnotations,
  runReadTool,
} from "../tool-runtime.js";
import { detailWidgetUri } from "../widget-resources.js";

export function registerCourseTools(server: McpServer) {
  registerAppTool(
    server,
    "get_course_catalog_filters",
    {
      outputSchema: outputSchemas.get_course_catalog_filters,
      title: "Get module catalog filters",
      description:
        "Use this before module discovery when you need the valid Alma filter values for degrees, subjects, faculties, languages, or element types.",
      inputSchema: {},
      annotations: readOnlyAnnotations(true),
      _meta: {},
    },
    async () =>
      runReadTool(async () => {
        const filters = await loadCourseCatalogFilters();
        return {
          structuredContent: asStructured(filters),
          content: [
            {
              type: "text" as const,
              text: "Loaded the current Alma module catalog filter options.",
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "search_courses",
    {
      outputSchema: outputSchemas.search_courses,
      title: "Search public Alma module catalog",
      description:
        "Use this when the user wants public module descriptions filtered by degree, subject, faculty, language, or element type.",
      inputSchema: {
        query: z.string().optional(),
        title: z.string().optional(),
        number: z.string().optional(),
        elementType: courseFilterListSchema,
        language: courseFilterListSchema,
        degree: courseFilterListSchema,
        subject: courseFilterListSchema,
        faculty: courseFilterListSchema,
        maxResults: z.number().int().min(1).max(50).optional(),
      },
      annotations: readOnlyAnnotations(true),
      _meta: {},
    },
    async (params) =>
      runReadTool(async () => {
        const results = await searchCourseCatalog(params);
        return {
          structuredContent: asStructured(results),
          content: [
            {
              type: "text" as const,
              text: `Loaded ${results.returnedResults} public Alma module results${results.totalResults !== null ? ` out of ${results.totalResults}` : ""}.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "search_course_offerings",
    {
      outputSchema: outputSchemas.search_course_offerings,
      title: "Search authenticated Alma course offerings",
      description:
        "Use this when the user wants live Alma course offerings for a term, such as current or upcoming lectures and searchable course detail URLs.",
      inputSchema: {
        query: z.string().optional(),
        term: z.string().optional(),
        limit: z.number().int().min(1).max(50).optional(),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ query, term, limit }) =>
      runReadTool(async () => {
        const results = await searchCourseOfferings({ query, term, limit });
        return {
          structuredContent: asStructured(results),
          content: [
            {
              type: "text" as const,
              text: `Loaded ${results.results.length} authenticated Alma course offerings for "${results.query}".`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_course_detail",
    {
      outputSchema: outputSchemas.get_course_detail,
      title: "Get Alma course detail",
      description:
        "Use this when the user already has an Alma detail URL and wants structured detail sections, including module/study-program assignments when Alma exposes them.",
      inputSchema: {
        url: z.string().url(),
      },
      annotations: readOnlyAnnotations(true),
      _meta: {
        ui: {
          resourceUri: detailWidgetUri,
        },
        "openai/outputTemplate": detailWidgetUri,
        "openai/toolInvocation/invoking": "Loading Alma detail…",
        "openai/toolInvocation/invoked": "Alma detail ready",
      },
    },
    async ({ url }) =>
      runReadTool(async () => {
        const detail = await loadCourseDetail(url);
        return {
          structuredContent: asStructured(detail),
          content: [
            {
              type: "text" as const,
              text: `Loaded Alma course detail for ${detail.title} with ${detail.module_study_program_tables.length} module/study-program assignment table(s).`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_combined_course_detail",
    {
      outputSchema: outputSchemas.get_combined_course_detail,
      title: "Get combined course detail",
      description:
        "Use this when the user wants one course page that combines Alma details with signup status across Alma, ILIAS, and Moodle.",
      inputSchema: {
        url: z.string().url().optional(),
        title: z.string().optional(),
        term: z.string().optional(),
        iliasLimit: z.number().int().min(1).max(12).optional(),
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ url, title, term, iliasLimit }) =>
      runReadTool(async () => {
        if (!url?.trim() && !title?.trim()) {
          throw new PortalBackendError("Provide an Alma detail URL or a course title.");
        }

        const bundle = await loadUnifiedCourseDetail({ url, title, term, iliasLimit });
        const signedUpCount = bundle.portal_statuses.filter((status) => status.signed_up === true).length;
        return {
          structuredContent: asStructured(bundle),
          content: [
            {
              type: "text" as const,
              text: `Loaded ${bundle.alma.title} with ${signedUpCount} signed-up portal status(es), ${bundle.ilias_results.length} related ILIAS result(s), and ${bundle.registration_hints.length} registration hint(s).`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_study_planner",
    {
      outputSchema: outputSchemas.get_study_planner,
      title: "Get Alma study planner",
      description:
        "Use this when the user wants the semester grid, recommended plan, or current module layout from Alma's study planner.",
      inputSchema: {},
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async () =>
      runReadTool(async () => {
        const planner = await loadStudyPlanner();
        return {
          structuredContent: asStructured(planner),
          content: [
            {
              type: "text" as const,
              text: `Loaded the Alma study planner with ${planner.modules.length} visible modules across ${planner.semesters.length} semesters.`,
            },
          ],
        };
      }),
  );
}
