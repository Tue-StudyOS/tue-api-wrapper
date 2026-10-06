import { outputSchemas } from "../tool-output-schemas.js";
import { registerAppTool } from "@modelcontextprotocol/ext-apps/server";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { loadCampusFoodPlan } from "../campus-backend.js";
import type { CampusCanteen, CampusFoodPlanPayload, CampusMenu } from "../types.js";
import { asStructured, readOnlyAnnotations, runReadTool } from "../tool-runtime.js";
import { mensaWidgetUri } from "../widget-resources.js";

const campusDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine((value) => {
  const date = new Date(`${value}T12:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}, "Use a valid calendar date in YYYY-MM-DD format.").optional();
const canteenIdsSchema = z.array(z.string().regex(/^\d+$/)).min(1).max(5).optional();
const iconsSchema = z.array(z.string().min(1)).min(1).max(4).optional();

function berlinToday(): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Berlin",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());

  const values = Object.fromEntries(
    parts
      .filter((part) => part.type === "year" || part.type === "month" || part.type === "day")
      .map((part) => [part.type, part.value]),
  );

  return `${values.year}-${values.month}-${values.day}`;
}

function menuMatchesIcons(menu: CampusMenu, requestedIcons: string[]): boolean {
  if (!requestedIcons.length) {
    return true;
  }

  const availableIcons = new Set(
    [...menu.icons, ...menu.filters_include].map((value) => value.trim().toLowerCase()).filter(Boolean),
  );
  return requestedIcons.every((icon) => availableIcons.has(icon));
}

function filterCanteens(
  canteens: CampusCanteen[],
  requestedCanteenIds: string[],
  requestedIcons: string[],
): CampusCanteen[] {
  return canteens
    .filter((canteen) => !requestedCanteenIds.length || requestedCanteenIds.includes(canteen.canteen_id))
    .map((canteen) => ({
      ...canteen,
      menus: canteen.menus.filter((menu) => menuMatchesIcons(menu, requestedIcons)),
    }));
}

function summarizeMenus(canteens: CampusCanteen[]): number {
  return canteens.reduce((total, canteen) => total + canteen.menus.length, 0);
}

export function registerCampusTools(server: McpServer) {
  registerAppTool(
    server,
    "get_mensa_food_plan",
    {
      outputSchema: outputSchemas.get_mensa_food_plan,
      title: "Get mensa food plan",
      description:
        "Use this when the user asks about mensa menus, cafeteria food, lunch options, or vegan and vegetarian meals in Tübingen.",
      inputSchema: {
        date: campusDateSchema,
        canteenIds: canteenIdsSchema,
        icons: iconsSchema,
      },
      annotations: readOnlyAnnotations(true),
      _meta: {
        ui: {
          resourceUri: mensaWidgetUri,
        },
        "openai/outputTemplate": mensaWidgetUri,
        "openai/toolInvocation/invoking": "Loading mensa plan…",
        "openai/toolInvocation/invoked": "Mensa plan ready",
      },
    },
    async ({ date, canteenIds, icons }) =>
      runReadTool(async () => {
        const targetDate = date ?? berlinToday();
        const requestedCanteenIds = (canteenIds ?? []).map((value) => value.trim()).filter(Boolean);
        const requestedIcons = (icons ?? []).map((value) => value.trim().toLowerCase()).filter(Boolean);
        const canteens = filterCanteens(
          await loadCampusFoodPlan({ date: targetDate }),
          requestedCanteenIds,
          requestedIcons,
        );
        const matchedMenuCount = summarizeMenus(canteens);
        const result: CampusFoodPlanPayload = {
          date: targetDate,
          canteens,
          matched_menu_count: matchedMenuCount,
          requested_canteen_ids: requestedCanteenIds,
          requested_icons: requestedIcons,
        };

        const iconSummary = requestedIcons.length ? ` matching ${requestedIcons.join(", ")}` : "";
        return {
          structuredContent: asStructured({
            view: "mensa",
            ...result,
          }),
          content: [
            {
              type: "text" as const,
              text:
                matchedMenuCount > 0
                  ? `Loaded ${matchedMenuCount} published menus across ${canteens.length} Tübingen canteens for ${targetDate}${iconSummary}.`
                  : `No published Tübingen mensa menus matched ${targetDate}${iconSummary}.`,
            },
          ],
        };
      }),
  );
}
