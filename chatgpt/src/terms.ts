// University semester boundaries: https://uni-tuebingen.de/en/843
export function currentStudyTerm(now = new Date()): string {
  const parts = new Intl.DateTimeFormat("en", { timeZone: "Europe/Berlin", year: "numeric", month: "numeric" }).formatToParts(now);
  const year = Number(parts.find(part => part.type === "year")!.value);
  const month = Number(parts.find(part => part.type === "month")!.value);
  if (month >= 4 && month <= 9) return `Sommer ${year}`;
  const start = month < 4 ? year - 1 : year;
  return `Winter ${start}/${String((start + 1) % 100).padStart(2, "0")}`;
}
export const defaultStudyTerm = currentStudyTerm();

const relativeStudyTerms = new Set([
  "aktuell",
  "aktuelles semester",
  "current",
  "current semester",
  "current term",
  "default",
  "dieses semester",
  "this semester",
  "this term",
]);

export function normalizeStudyTerm(term: string | null | undefined, fallback = currentStudyTerm()): string {
  const raw = term?.trim();
  if (!raw) {
    return fallback;
  }

  const cleaned = raw.replace(/\s+/g, " ").replace(/[.,;:]$/, "");
  const key = cleaned
    .toLowerCase()
    .replace(/[._-]+/g, " ")
    .replace(/\s+/g, " ");

  if (relativeStudyTerms.has(key)) {
    return fallback;
  }

  const summerMatch = key.match(/^(?:sommer|summer|sommer semester|sommersemester|sommersemster|somersemester|sose|ss)\s*(\d{4})$/);
  if (summerMatch) {
    return `Sommer ${summerMatch[1]}`;
  }

  const winterMatch = key.match(/^(?:winter|winter semester|wintersemester|wise|ws)\s*(\d{4})(?:\s*\/?\s*(\d{2,4}))?$/);
  if (winterMatch) {
    const startYear = winterMatch[1];
    const endYear = winterMatch[2] ?? String((Number(startYear) + 1) % 100).padStart(2, "0");
    return `Winter ${startYear}/${endYear.slice(-2)}`;
  }

  return cleaned;
}

export function normalizeOptionalStudyTerm(term: string | null | undefined): string | undefined {
  return term?.trim() ? normalizeStudyTerm(term) : undefined;
}
