import type { CampusCanteen } from "./types.js";
import { fetchPortalJson } from "./backend-http.js";

export interface CampusFoodPlanParams {
  date?: string;
}

function buildCampusQueryString(params: CampusFoodPlanParams): string {
  const query = new URLSearchParams();
  if (params.date?.trim()) {
    query.set("date", params.date.trim());
  }
  const suffix = query.toString();
  return suffix ? `?${suffix}` : "";
}

export async function loadCampusFoodPlan(params: CampusFoodPlanParams = {}): Promise<CampusCanteen[]> {
  return fetchPortalJson<CampusCanteen[]>(
    `/api/campus/canteens${buildCampusQueryString(params)}`,
  );
}
