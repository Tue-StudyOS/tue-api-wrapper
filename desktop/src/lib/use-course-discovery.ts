import { useCallback, useEffect, useState } from "react";

import { fetchCourseDiscoveryStatus, refreshCourseDiscoveryIndex, searchCourseDiscovery } from "./api";
import type { CourseDiscoverySearchResponse, CourseDiscoveryStatus } from "./course-discovery-types";

export function useCourseDiscovery(baseUrl: string | null, enabled: boolean) {
  const [query, setQuery] = useState("machine learning");
  const [sources, setSources] = useState<string[]>(["alma", "ilias", "moodle"]);
  const [includePrivate, setIncludePrivate] = useState(true);
  const [degrees, setDegrees] = useState<string[]>([]);
  const [moduleCodes, setModuleCodes] = useState<string[]>([]);
  const [response, setResponse] = useState<CourseDiscoverySearchResponse | null>(null);
  const [status, setStatus] = useState<CourseDiscoveryStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    if (!baseUrl || !enabled) {
      return;
    }
    try {
      setStatus(await fetchCourseDiscoveryStatus(baseUrl));
    } catch {
      setStatus(null);
    }
  }, [baseUrl, enabled]);

  const search = useCallback(async () => {
    if (!baseUrl || !enabled || !query.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const next = await searchCourseDiscovery(baseUrl, {
        query: query.trim(),
        sources,
        degrees,
        moduleCodes,
        includePrivate
      });
      setResponse(next);
      setStatus(next.status);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Could not search course discovery.");
    } finally {
      setLoading(false);
    }
  }, [baseUrl, degrees, enabled, includePrivate, moduleCodes, query, sources]);

  const sync = useCallback(async () => {
    if (!baseUrl || !enabled) {
      return;
    }
    setSyncing(true);
    setError(null);
    try {
      setStatus(await refreshCourseDiscoveryIndex(baseUrl, { includePrivate }));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Could not sync course discovery index.");
    } finally {
      setSyncing(false);
    }
  }, [baseUrl, enabled, includePrivate]);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  return {
    error,
    includePrivate,
    degrees,
    loading,
    moduleCodes,
    query,
    response,
    search,
    setIncludePrivate,
    setDegrees,
    setModuleCodes,
    setQuery,
    setSources,
    sources,
    sync,
    syncing,
    status
  };
}
