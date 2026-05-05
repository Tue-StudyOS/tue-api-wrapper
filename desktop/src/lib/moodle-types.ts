export interface MoodleDashboardEvent {
  id: number | null;
  title: string;
  due_at: string | null;
  formatted_time: string | null;
  course_name: string | null;
  course_id: number | null;
  action_url: string | null;
  description: string | null;
  is_actionable: boolean;
}

export interface MoodleRecentItem {
  id: number | null;
  title: string;
  item_type: string | null;
  course_name: string | null;
  course_id: number | null;
  url: string | null;
  icon_url: string | null;
}

export interface MoodleCourseSummary {
  id: number | null;
  title: string;
  shortname: string | null;
  category_name: string | null;
  visible: boolean | null;
  end_date: string | null;
  url: string | null;
  image_url: string | null;
  summary?: string | null;
  teachers?: string[];
}

export interface MoodleDashboardData {
  source_url: string;
  events: MoodleDashboardEvent[];
  recent_items: MoodleRecentItem[];
  courses: MoodleCourseSummary[];
}

export interface MoodleGradeItem {
  course_title: string;
  grade: string | null;
  percentage: string | null;
  range_hint: string | null;
  rank: string | null;
  feedback: string | null;
  url: string | null;
}

export interface MoodleGradesResponse {
  source_url: string;
  items: MoodleGradeItem[];
}

export interface MoodleMessagesResponse {
  source_url: string;
  items: Array<{
    title: string;
    preview: string | null;
    sender: string | null;
    timestamp: string | null;
    url: string | null;
    unread: boolean | null;
  }>;
}

export interface MoodleNotificationsResponse {
  source_url: string;
  items: Array<{
    title: string;
    body: string | null;
    timestamp: string | null;
    url: string | null;
    unread: boolean | null;
  }>;
}

export interface MoodleSnapshot {
  dashboard?: MoodleDashboardData;
  grades?: MoodleGradesResponse;
  messages?: MoodleMessagesResponse;
  notifications?: MoodleNotificationsResponse;
  errors: string[];
}
