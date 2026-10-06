import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import {
  loadDashboard,
  loadDocumentsSummary,
  loadMemberships,
  loadTasks,
  loadTimetable,
} from "../backend.js";
import {
  asStructured,
  buildSnapshot,
  limitSchema,
  readOnlyAnnotations,
  runReadTool,
} from "../tool-runtime.js";

export function registerStudyTools(server: McpServer) {
  registerAppTool(
    server,
    "get_study_snapshot",
    {
      outputSchema: outputSchemas.get_study_snapshot,
      title: "Get study snapshot",
      description:
        "Use this when the user asks for an overall status update or combines multiple questions about upcoming lectures, open tasks, grades, and learning spaces.",
      inputSchema: {
        term: z.string().min(1).optional(),
        limit: limitSchema,
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ term, limit }) =>
      runReadTool(async () => {
        const dashboard = await loadDashboard(term);
        const snapshot = buildSnapshot(dashboard, limit ?? 5);
        return {
          structuredContent: snapshot,
          content: [
            {
              type: "text" as const,
              text: `Loaded a study snapshot for ${dashboard.termLabel} with ${snapshot.nextEvents.length} upcoming events, ${snapshot.openTasks.length} tasks, and ${snapshot.grades.length} recent exam rows.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_upcoming_schedule",
    {
      outputSchema: outputSchemas.get_upcoming_schedule,
      title: "Get upcoming schedule",
      description:
        "Use this when the user asks about next lectures, meetings, classes, or calendar items from Alma.",
      inputSchema: {
        term: z.string().min(1).optional(),
        limit: limitSchema,
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ term, limit }) =>
      runReadTool(async () => {
        const timetable = await loadTimetable(term);
        const items = timetable.occurrences.slice(0, limit ?? 5);
        return {
          structuredContent: {
            termLabel: timetable.term_label,
            exportUrl: timetable.export_url,
            items,
          },
          content: [
            {
              type: "text" as const,
              text: `Loaded ${items.length} upcoming Alma schedule items for ${timetable.term_label}.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_current_tasks",
    {
      outputSchema: outputSchemas.get_current_tasks,
      title: "Get current tasks",
      description:
        "Use this when the user asks about open ILIAS tasks, due items, or assignment deadlines.",
      inputSchema: {
        limit: limitSchema,
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ limit }) =>
      runReadTool(async () => {
        const tasks = await loadTasks(limit ?? 8);
        return {
          structuredContent: {
            tasks,
          },
          content: [
            {
              type: "text" as const,
              text: `Loaded ${tasks.length} ILIAS tasks.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_current_grades",
    {
      outputSchema: outputSchemas.get_current_grades,
      title: "Get current grades",
      description:
        "Use this when the user asks about grades, passed exams, credits, or current Alma study progress.",
      inputSchema: {
        limit: limitSchema,
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ limit }) =>
      runReadTool(async () => {
        const dashboard = await loadDashboard(undefined, limit ?? 8);
        const exams = dashboard.exams;
        const { passedExamCount, trackedCredits } = dashboard.study;
        return {
          structuredContent: {
            study: {
              selectedTerm: dashboard.study.selectedTerm ?? dashboard.enrollment.selected_term,
              message: dashboard.study.message ?? dashboard.enrollment.message,
              passedExamCount,
              trackedCredits,
              currentSemesterCredits: dashboard.study.currentSemesterCredits,
              currentSemesterCreditCourses: dashboard.study.currentSemesterCreditCourses,
              currentSemesterCreditUnresolved: dashboard.study.currentSemesterCreditUnresolved,
              currentSemesterCreditError: dashboard.study.currentSemesterCreditError,
            },
            exams,
          },
          content: [
            {
              type: "text" as const,
              text: `Loaded ${exams.length} visible exam rows; the full leaf-record overview has ${trackedCredits} tracked credits, ${dashboard.study.currentSemesterCredits ?? "unknown"} saved-semester credits, and ${passedExamCount} passed exams.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_learning_spaces",
    {
      outputSchema: outputSchemas.get_learning_spaces,
      title: "Get learning spaces",
      description:
        "Use this when the user asks which ILIAS courses, groups, or learning spaces they currently belong to.",
      inputSchema: {
        limit: limitSchema,
      },
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async ({ limit }) =>
      runReadTool(async () => {
        const memberships = await loadMemberships(limit ?? 8);
        return {
          structuredContent: {
            memberships,
          },
          content: [
            {
              type: "text" as const,
              text: `Loaded ${memberships.length} ILIAS memberships.`,
            },
          ],
        };
      }),
  );

  registerAppTool(
    server,
    "get_documents_summary",
    {
      outputSchema: outputSchemas.get_documents_summary,
      title: "Get study-service documents summary",
      description:
        "Use this when the user wants Alma document jobs, transcript options, output-request groups, or the current study-service PDF.",
      inputSchema: {},
      annotations: readOnlyAnnotations(),
      _meta: {},
    },
    async () =>
      runReadTool(async () => {
        const documents = await loadDocumentsSummary();
        const availableCount =
          documents.reports.length +
          documents.outputRequests.length +
          (documents.currentDownloadAvailable ? 1 : 0);
        return {
          structuredContent: asStructured(documents),
          content: [
            {
              type: "text" as const,
              text: availableCount
                ? `Loaded ${documents.reports.length} Alma study-service report jobs, ${documents.outputRequests.length} output-request groups, and ${documents.currentDownloadAvailable ? "a current PDF download" : "no current PDF download"}.`
                : "The Alma study-service page loaded, but no report jobs, output-request groups, or current PDF downloads are currently available.",
            },
          ],
        };
      }),
  );
}
