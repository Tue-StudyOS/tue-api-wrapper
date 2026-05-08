import { useEffect, useState } from "react";

import { fetchCareerFilters, fetchCareerProject, searchCareerProjects } from "./career-api";
import type { CareerProjectDetail, CareerSearchFilters, CareerSearchResponse } from "./career-types";

export function useCareerSearch(baseUrl: string | null, enabled: boolean) {
  const [query, setQuery] = useState("");
  const [projectTypeId, setProjectTypeId] = useState<number | null>(null);
  const [projectSubtypeId, setProjectSubtypeId] = useState<number | null>(null);
  const [industryId, setIndustryId] = useState<number | null>(null);
  const [postalCode, setPostalCode] = useState("");
  const [response, setResponse] = useState<CareerSearchResponse | null>(null);
  const [filters, setFilters] = useState<CareerSearchFilters | null>(null);
  const [detail, setDetail] = useState<CareerProjectDetail | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (enabled && baseUrl && !response) {
      void refresh();
    }
  }, [baseUrl, enabled]);

  async function refresh(page = 0) {
    if (!baseUrl) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [nextFilters, nextResponse] = await Promise.all([
        filters ? Promise.resolve(filters) : fetchCareerFilters(baseUrl),
        searchCareerProjects(baseUrl, { query, projectTypeId, projectSubtypeId, industryId, postalCode, page })
      ]);
      setFilters(nextFilters);
      setResponse(nextResponse);
      setDetail(null);
      setSelectedId(null);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Praxisportal lookup failed.");
    } finally {
      setLoading(false);
    }
  }

  async function selectProject(projectId: number) {
    if (!baseUrl) {
      return;
    }
    setSelectedId(projectId);
    setDetailLoading(true);
    setError(null);
    try {
      setDetail(await fetchCareerProject(baseUrl, projectId));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Praxisportal listing failed.");
    } finally {
      setDetailLoading(false);
    }
  }

  function clearSelection() {
    setSelectedId(null);
    setDetail(null);
    setDetailLoading(false);
  }

  return {
    clearSelection,
    detail,
    detailLoading,
    error,
    filters,
    industryId,
    loading,
    postalCode,
    projectSubtypeId,
    projectTypeId,
    query,
    refresh,
    response,
    selectedId,
    selectProject,
    setIndustryId,
    setPostalCode,
    setProjectSubtypeId,
    setProjectTypeId,
    setQuery
  };
}
