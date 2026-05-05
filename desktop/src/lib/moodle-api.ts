import { fetchJson } from "./api";
import type {
  MoodleDashboardData,
  MoodleGradesResponse,
  MoodleMessagesResponse,
  MoodleNotificationsResponse,
  MoodleSnapshot
} from "./moodle-types";

export async function fetchMoodleSnapshot(baseUrl: string): Promise<MoodleSnapshot> {
  const errors: string[] = [];
  const [dashboard, grades, messages, notifications] = await Promise.all([
    fetchJson<MoodleDashboardData>(baseUrl, "/api/moodle/dashboard").catch((error) => {
      errors.push(errorMessage("Moodle dashboard", error));
      return undefined;
    }),
    fetchJson<MoodleGradesResponse>(baseUrl, "/api/moodle/grades").catch((error) => {
      errors.push(errorMessage("Moodle grades", error));
      return undefined;
    }),
    fetchJson<MoodleMessagesResponse>(baseUrl, "/api/moodle/messages").catch((error) => {
      errors.push(errorMessage("Moodle messages", error));
      return undefined;
    }),
    fetchJson<MoodleNotificationsResponse>(baseUrl, "/api/moodle/notifications").catch((error) => {
      errors.push(errorMessage("Moodle notifications", error));
      return undefined;
    })
  ]);
  return { dashboard, grades, messages, notifications, errors };
}

function errorMessage(scope: string, error: unknown): string {
  return `${scope}: ${error instanceof Error ? error.message : "Request failed."}`;
}
