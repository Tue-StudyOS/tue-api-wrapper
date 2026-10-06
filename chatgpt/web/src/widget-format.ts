export function escapeHtml(value: string | null | undefined): string {
  return (value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function encodeData(value: unknown): string {
  return encodeURIComponent(JSON.stringify(value));
}

export function decodeData<T>(value: string | undefined): T | null {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(decodeURIComponent(value)) as T;
  } catch {
    return null;
  }
}

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Date pending";
  }
  return new Intl.DateTimeFormat("de-DE", {
    timeZone: "Europe/Berlin",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

export function formatRelativeStart(value: string): string | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  const relative = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const diffMinutes = Math.round((date.getTime() - Date.now()) / (1000 * 60));

  if (Math.abs(diffMinutes) < 60) {
    return relative.format(diffMinutes, "minute");
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 48) {
    return relative.format(diffHours, "hour");
  }

  return relative.format(Math.round(diffHours / 24), "day");
}

export function formatCredits(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "Unavailable";
  }
  return `${Number.isInteger(value) ? value : value.toFixed(1).replace(/\.0$/, "")} CP`;
}
