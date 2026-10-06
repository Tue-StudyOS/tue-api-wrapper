import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import {
  loadAlmaRegistrationSupport,
  loadIliasWaitlistSupport,
  loadMoodleEnrolmentSupport,
} from "../action-backend.js";
import { PortalBackendError } from "../backend.js";
import { actionWidgetUri } from "../widget-resources.js";
import { toolErrorResponse } from "../tool-runtime.js";
import {
  actionAnnotations,
  consumePendingAction,
  prepareTool,
  storeAction,
} from "./critical-action-store.js";

export function registerActionTools(server: McpServer) {
  registerAppTool(
    server,
    "prepare_alma_course_registration",
    {
      outputSchema: outputSchemas.prepare_alma_course_registration,
      title: "Prepare Alma course registration",
      description:
        "Use this when the user wants to register for an Alma course. This only renders a confirmation UI; it never registers until the user presses Proceed.",
      inputSchema: {
        url: z.string().url(),
        planelementId: z.string().optional(),
      },
      annotations: actionAnnotations(false),
      _meta: {
        ui: { resourceUri: actionWidgetUri },
        "openai/outputTemplate": actionWidgetUri,
        "openai/toolInvocation/invoking": "Preparing confirmation…",
        "openai/toolInvocation/invoked": "Confirmation ready",
      },
    },
    async ({ url, planelementId }) =>
      prepareTool(async () => {
        const support = await loadAlmaRegistrationSupport(url);
        if (!support.supported) {
          throw new PortalBackendError(support.message ?? "This Alma page does not expose registration.");
        }
        return storeAction(
          {
            kind: "alma_course_registration",
            portal: "Alma",
            title: support.title ?? support.number ?? "Alma course",
            actionLabel: "Register for Alma course",
            targetUrl: support.detail_url,
            endpoint: "/api/alma/course-registration",
            method: "POST",
            sideEffects: [
              "Submits an Alma course-registration request for the signed-in university account.",
              "Uses the displayed Alma detail page and selected registration path.",
              "If Alma exposes multiple paths and none is selected, the backend will stop with an error instead of guessing.",
            ],
            requiredInputs: planelementId ? [`Registration path ${planelementId}`] : [],
          },
          { kind: "alma_course_registration", url: support.detail_url, planelementId },
        );
      }),
  );

  registerAppTool(
    server,
    "prepare_ilias_waitlist_join",
    {
      outputSchema: outputSchemas.prepare_ilias_waitlist_join,
      title: "Prepare ILIAS waitlist join",
      description:
        "Use this when the user wants to join an ILIAS course waitlist. This only renders a confirmation UI until the user presses Proceed.",
      inputSchema: {
        url: z.string().min(1),
      },
      annotations: actionAnnotations(false),
      _meta: {
        ui: { resourceUri: actionWidgetUri },
        "openai/outputTemplate": actionWidgetUri,
      },
    },
    async ({ url }) =>
      prepareTool(async () => {
        const support = await loadIliasWaitlistSupport(url);
        if (!support.supported) {
          throw new PortalBackendError(support.message ?? "This ILIAS page does not expose a waitlist join action.");
        }
        if (support.requires_agreement) {
          throw new PortalBackendError("Open this ILIAS page and read and accept its usage agreement yourself before preparing the waitlist action again.");
        }
        return storeAction(
          {
            kind: "ilias_waitlist_join",
            portal: "ILIAS",
            title: "ILIAS waitlist",
            actionLabel: "Join ILIAS waitlist",
            targetUrl: support.join_url ?? url,
            endpoint: "/api/ilias/waitlist/join",
            method: "POST",
            sideEffects: [
              "Submits a waitlist join request in ILIAS for the signed-in university account.",
            ],
            requiredInputs: [],
          },
          { kind: "ilias_waitlist_join", url },
        );
      }),
  );

  registerAppTool(
    server,
    "prepare_ilias_add_favorite",
    {
      outputSchema: outputSchemas.prepare_ilias_add_favorite,
      title: "Prepare ILIAS favorite",
      description:
        "Use this when the user wants to add an ILIAS item to favorites. This only renders a confirmation UI until the user presses Proceed.",
      inputSchema: { url: z.string().min(1) },
      annotations: actionAnnotations(false),
      _meta: {
        ui: { resourceUri: actionWidgetUri },
        "openai/outputTemplate": actionWidgetUri,
      },
    },
    async ({ url }) =>
      prepareTool(async () =>
        storeAction(
          {
            kind: "ilias_add_favorite",
            portal: "ILIAS",
            title: "ILIAS item",
            actionLabel: "Add ILIAS favorite",
            targetUrl: url,
            endpoint: "/api/ilias/favorites",
            method: "POST",
            sideEffects: ["Adds the selected ILIAS item to the signed-in account's favorites or desktop."],
            requiredInputs: [],
          },
          { kind: "ilias_add_favorite", url },
        ),
      ),
  );

  registerAppTool(
    server,
    "prepare_moodle_course_enrolment",
    {
      outputSchema: outputSchemas.prepare_moodle_course_enrolment,
      title: "Prepare Moodle course enrolment",
      description:
        "Use this when the user wants to self-enrol in a Moodle course. This only renders a confirmation UI until the user presses Proceed.",
      inputSchema: {
        courseId: z.number().int().positive(),
      },
      annotations: actionAnnotations(false),
      _meta: {
        ui: { resourceUri: actionWidgetUri },
        "openai/outputTemplate": actionWidgetUri,
      },
    },
    async ({ courseId }) =>
      prepareTool(async () => {
        const support = await loadMoodleEnrolmentSupport(courseId);
        if (!support.self_enrolment_available) {
          throw new PortalBackendError("This Moodle course does not expose self-enrolment.");
        }
        return storeAction(
          {
            kind: "moodle_course_enrolment",
            portal: "Moodle",
            title: support.title,
            actionLabel: "Enrol in Moodle course",
            targetUrl: support.course_url ?? support.source_url,
            endpoint: `/api/moodle/course/${courseId}/enrol`,
            method: "POST",
            sideEffects: ["Submits Moodle self-enrolment for the signed-in university account."],
            requiredInputs: support.requires_enrolment_key ? ["Enter the course enrolment key in this confirmation widget."] : [],
            requiresEnrolmentKey: support.requires_enrolment_key,
          },
          { kind: "moodle_course_enrolment", courseId },
        );
      }),
  );

  registerAppTool(
    server,
    "confirm_critical_action",
    {
      outputSchema: outputSchemas.confirm_critical_action,
      title: "Confirm critical action",
      description:
        "Use only from the confirmation widget after the user presses Proceed. It executes the prepared action exactly once.",
      inputSchema: {
        intentId: z.string().min(1),
        confirmationToken: z.string().min(1),
        enrolmentKey: z.string().max(256).optional(),
      },
      annotations: actionAnnotations(true),
      _meta: {
        ui: { visibility: ["app"] },
        "openai/widgetAccessible": true,
      },
    },
    async ({ intentId, confirmationToken, enrolmentKey }) => {
      try {
        const stored = consumePendingAction(intentId, confirmationToken);
        if (stored.intent.requiresEnrolmentKey && !enrolmentKey) {
          throw new PortalBackendError("An enrolment key is required. Prepare the action again and enter the key in its widget.");
        }
        const result = await stored.execute(enrolmentKey);
        return {
          structuredContent: {
            status: "completed",
            kind: stored.intent.kind,
            intent: stored.intent,
            result,
          },
          content: [
            {
              type: "text" as const,
              text: `${stored.intent.actionLabel} finished with status ${result.status}.`,
            },
          ],
          _meta: { result },
        };
      } catch (error) {
        if (error instanceof PortalBackendError) {
          return toolErrorResponse(error);
        }
        return toolErrorResponse(new PortalBackendError("The action result could not be verified. Check the university portal before trying again."));
      }
    },
  );

  registerAppTool(
    server,
    "cancel_critical_action",
    {
      outputSchema: outputSchemas.cancel_critical_action,
      title: "Cancel prepared action",
      description: "Discard a prepared action when the user presses Cancel in its confirmation widget.",
      inputSchema: { intentId: z.string().min(1), confirmationToken: z.string().min(1) },
      annotations: actionAnnotations(false),
      _meta: { ui: { visibility: ["app"] }, "openai/widgetAccessible": true },
    },
    async ({ intentId, confirmationToken }) => {
      try {
        consumePendingAction(intentId, confirmationToken);
        return { structuredContent: { status: "cancelled" }, content: [{ type: "text" as const, text: "The prepared action was discarded. No university action was submitted." }] };
      } catch (error) {
        return toolErrorResponse(error instanceof PortalBackendError ? error : new PortalBackendError("The action could not be cancelled."));
      }
    },
  );
}
