import { fetchJson } from "./api";
import type { CareerProjectDetail, CareerSearchFilters, CareerSearchResponse } from "./career-types";

export async function fetchCareerFilters(baseUrl: string): Promise<CareerSearchFilters> {
  return fetchJson<CareerSearchFilters>(baseUrl, "/api/praxisportal/filters");
}

export async function searchCareerProjects(
  baseUrl: string,
  input: {
    query: string;
    projectTypeId: number | null;
    projectSubtypeId: number | null;
    industryId: number | null;
    postalCode: string;
    page: number;
    perPage?: number;
  }
): Promise<CareerSearchResponse> {
  const params = new URLSearchParams({
    query: input.query.trim(),
    page: String(input.page),
    per_page: String(input.perPage ?? 20)
  });
  if (input.projectTypeId) {
    params.append("project_type_id", String(input.projectTypeId));
  }
  if (input.projectSubtypeId) {
    params.append("project_subtype_id", String(input.projectSubtypeId));
  }
  if (input.industryId) {
    params.append("industry_id", String(input.industryId));
  }
  if (input.postalCode.trim()) {
    params.append("postal_code", input.postalCode.trim());
  }
  return fetchJson<CareerSearchResponse>(baseUrl, `/api/praxisportal/search?${params.toString()}`);
}

export async function fetchCareerProject(baseUrl: string, projectId: number): Promise<CareerProjectDetail> {
  return fetchJson<CareerProjectDetail>(baseUrl, `/api/praxisportal/projects/${projectId}`);
}
