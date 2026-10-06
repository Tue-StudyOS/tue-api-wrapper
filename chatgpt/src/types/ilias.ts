export interface IliasLink {
  label: string;
  url: string;
}

export interface IliasMembershipItem {
  title: string;
  url: string;
  kind: string | null;
  description: string | null;
  info_url: string | null;
  properties: string[];
}

export interface IliasTaskItem {
  title: string;
  url: string;
  item_type: string | null;
  start: string | null;
  end: string | null;
}

export interface IliasContentItem {
  label: string;
  url: string;
  kind: string | null;
  properties: string[];
}

export interface IliasContentSection {
  label: string;
  items: IliasContentItem[];
}

export interface IliasContentPage {
  title: string;
  page_url: string;
  sections: IliasContentSection[];
}

export interface IliasForumTopic {
  title: string;
  url: string;
  author: string | null;
  posts: string | null;
  last_post: string | null;
  visits: string | null;
}

export interface IliasExerciseAssignment {
  title: string;
  url: string;
  due_hint: string | null;
  due_at: string | null;
  requirement: string | null;
  last_submission: string | null;
  submission_type: string | null;
  status: string | null;
  team_action_url: string | null;
}

export interface IliasSearchOption {
  value: string;
  label: string;
  is_selected: boolean;
}

export interface IliasSearchFilters {
  area_value: string | null;
  area_label: string | null;
  search_modes: IliasSearchOption[];
  content_types: IliasSearchOption[];
  creation_modes: IliasSearchOption[];
  creation_enabled: boolean;
  creation_date: string | null;
}

export interface IliasSearchResult {
  title: string;
  url: string | null;
  description: string | null;
  info_url: string | null;
  add_to_favorites_url: string | null;
  breadcrumbs: string[];
  properties: string[];
  item_type: string | null;
}

export interface IliasSearchResponse {
  page_url: string;
  query: string;
  page_number: number;
  previous_page_url: string | null;
  next_page_url: string | null;
  filters: IliasSearchFilters;
  results: IliasSearchResult[];
}

export interface LearningSpaceInspection {
  errors: Partial<Record<"content" | "forum" | "exercise", string>>;
  content: IliasContentPage | null;
  forum: IliasForumTopic[];
  exercise: IliasExerciseAssignment[];
}
