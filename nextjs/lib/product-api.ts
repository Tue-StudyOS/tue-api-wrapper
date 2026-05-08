import {
  buildPortalApiUrl,
  PortalApiError
} from "./portal-api";
import type {
  CampusBuildingDetail,
  CampusBuildingDirectory,
  CampusCanteen,
  CareerProjectDetail,
  CareerSearchFilters,
  CareerSearchResponse,
  KufTrainingOccupancy,
  Talk,
  TalksResponse,
  TimmsItemDetail,
  TimmsSearchResponse,
  TimmsStreamVariant,
  TimmsTreeResponse,
  UniversityCalendarResponse
} from "./product-types";

async function fetchProductJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildPortalApiUrl(path), { cache: "no-store" });
  } catch {
    throw new PortalApiError(
      `Could not reach the backend at ${buildPortalApiUrl("")}. Start the Python API or set PORTAL_API_BASE_URL correctly.`
    );
  }

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new PortalApiError(
      `Backend request failed for ${path} with ${response.status}${detail ? `: ${detail}` : ""}`
    );
  }

  return (await response.json()) as T;
}

export function getTimmsSearch(query: string, limit = 20): Promise<TimmsSearchResponse> {
  const params = new URLSearchParams({ query, limit: String(limit) });
  return fetchProductJson(`/api/timms/search?${params.toString()}`);
}

export async function getTimmsSuggestions(term: string, limit = 8): Promise<string[]> {
  const params = new URLSearchParams({ term, limit: String(limit) });
  const payload = await fetchProductJson<{ items: string[] }>(`/api/timms/search/suggest?${params.toString()}`);
  return payload.items;
}

export function getTimmsItem(itemId: string): Promise<TimmsItemDetail> {
  return fetchProductJson(`/api/timms/items/${encodeURIComponent(itemId)}`);
}

export function getTimmsStreams(itemId: string): Promise<TimmsStreamVariant[]> {
  return fetchProductJson(`/api/timms/items/${encodeURIComponent(itemId)}/streams`);
}

export function getTimmsTree(options: { nodeId?: string; nodePath?: string } = {}): Promise<TimmsTreeResponse> {
  const params = new URLSearchParams();
  if (options.nodeId?.trim()) {
    params.set("node_id", options.nodeId.trim());
  }
  if (options.nodePath?.trim()) {
    params.set("node_path", options.nodePath.trim());
  }
  return fetchProductJson(`/api/timms/tree${params.size ? `?${params.toString()}` : ""}`);
}

export function getTalks(options: {
  scope?: string;
  query?: string;
  tagIds?: number[];
  limit?: number;
} = {}): Promise<TalksResponse> {
  const params = new URLSearchParams();
  params.set("scope", options.scope ?? "upcoming");
  params.set("limit", String(options.limit ?? 50));
  if (options.query?.trim()) {
    params.set("query", options.query.trim());
  }
  for (const id of options.tagIds ?? []) {
    params.append("tag_id", String(id));
  }
  return fetchProductJson(`/api/talks?${params.toString()}`);
}

export function getTalk(talkId: number): Promise<Talk> {
  return fetchProductJson(`/api/talks/${talkId}`);
}

export function getCareerFilters(): Promise<CareerSearchFilters> {
  return fetchProductJson("/api/praxisportal/filters");
}

export function getCareerSearch(options: {
  query?: string;
  projectTypeIds?: number[];
  projectSubtypeIds?: number[];
  industryIds?: number[];
  postalCodes?: string[];
  organizationIds?: number[];
  page?: number;
  perPage?: number;
} = {}): Promise<CareerSearchResponse> {
  const params = new URLSearchParams();
  if (options.query?.trim()) {
    params.set("query", options.query.trim());
  }
  for (const id of options.projectTypeIds ?? []) {
    params.append("project_type_id", String(id));
  }
  for (const id of options.projectSubtypeIds ?? []) {
    params.append("project_subtype_id", String(id));
  }
  for (const id of options.industryIds ?? []) {
    params.append("industry_id", String(id));
  }
  for (const code of options.postalCodes ?? []) {
    params.append("postal_code", code);
  }
  for (const id of options.organizationIds ?? []) {
    params.append("organization_id", String(id));
  }
  params.set("page", String(options.page ?? 0));
  params.set("per_page", String(options.perPage ?? 20));
  params.set("sort", "newest");
  return fetchProductJson(`/api/praxisportal/search?${params.toString()}`);
}

export function getCareerProject(projectId: number): Promise<CareerProjectDetail> {
  return fetchProductJson(`/api/praxisportal/projects/${projectId}`);
}

export function getCampusCanteens(): Promise<CampusCanteen[]> {
  return fetchProductJson("/api/campus/canteens");
}

export function getCampusBuildings(): Promise<CampusBuildingDirectory> {
  return fetchProductJson("/api/campus/buildings");
}

export function getCampusBuildingDetail(path: string): Promise<CampusBuildingDetail> {
  const params = new URLSearchParams({ path });
  return fetchProductJson(`/api/campus/buildings/detail?${params.toString()}`);
}

export function getKufTrainingOccupancy(): Promise<KufTrainingOccupancy> {
  return fetchProductJson("/api/campus/fitness/kuf");
}

export function getUniversityEvents(options: {
  query?: string;
  limit?: number;
} = {}): Promise<UniversityCalendarResponse> {
  const params = new URLSearchParams({ limit: String(options.limit ?? 50) });
  if (options.query?.trim()) {
    params.set("query", options.query.trim());
  }
  return fetchProductJson(`/api/campus/events?${params.toString()}`);
}
