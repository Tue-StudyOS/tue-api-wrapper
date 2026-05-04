import { useEffect, useState } from "react";

import { fetchMoodleSnapshot } from "./moodle-api";
import type { MoodleSnapshot } from "./moodle-types";

export function useMoodleSnapshot(baseUrl: string | null, enabled: boolean) {
  const [data, setData] = useState<MoodleSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (enabled && baseUrl && !data) {
      void refresh();
    }
  }, [baseUrl, enabled]);

  async function refresh() {
    if (!baseUrl) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await fetchMoodleSnapshot(baseUrl));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Moodle lookup failed.");
    } finally {
      setLoading(false);
    }
  }

  return { data, error, loading, refresh };
}
