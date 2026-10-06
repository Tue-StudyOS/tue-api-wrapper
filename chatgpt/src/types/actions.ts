export type CriticalActionKind =
  | "alma_course_registration"
  | "ilias_add_favorite"
  | "ilias_waitlist_join"
  | "moodle_course_enrolment";

export interface CriticalActionPublicIntent {
  id: string;
  kind: CriticalActionKind;
  portal: "Alma" | "ILIAS" | "Moodle";
  title: string;
  actionLabel: string;
  targetUrl: string | null;
  endpoint: string;
  method: "POST";
  sideEffects: string[];
  requiredInputs: string[];
  requiresEnrolmentKey?: boolean;
  preparedAt: string;
  expiresAt: string;
}

export interface CriticalActionView {
  view: "critical-action";
  intent: CriticalActionPublicIntent;
}

export interface CriticalActionResult {
  status: string;
  message: string | null;
  finalUrl: string | null;
  raw: Record<string, unknown>;
}
