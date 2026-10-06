import { addIliasFavorite, enrolInMoodleCourse, joinIliasWaitlist, registerForAlmaCourse } from "../action-backend.js";
import type { CriticalActionKind } from "../types/actions.js";
export interface ActionCommand { kind: CriticalActionKind; url?: string; planelementId?: string; courseId?: number; }
export function executeAction(command: ActionCommand, enrolmentKey?: string) {
  switch (command.kind) {
    case "alma_course_registration": return registerForAlmaCourse(command.url!, command.planelementId);
    case "ilias_add_favorite": return addIliasFavorite(command.url!);
    case "ilias_waitlist_join": return joinIliasWaitlist(command.url!, false);
    case "moodle_course_enrolment": return enrolInMoodleCourse(command.courseId!, enrolmentKey);
  }
}
