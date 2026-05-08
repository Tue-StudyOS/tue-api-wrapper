export interface TimmsChapter {
  start_seconds: number | null;
  start_label: string;
  title: string;
  url: string;
}

export interface TimmsSearchResult {
  item_id: string;
  title: string;
  item_url: string;
  preview_image_url: string | null;
  duration_label: string | null;
  chapters: TimmsChapter[];
}

export interface TimmsSearchResponse {
  query: string;
  total_hits: number;
  offset: number;
  limit: number;
  source_url: string;
  results: TimmsSearchResult[];
}

export interface TimmsMetadataField {
  label: string;
  value: string;
  url: string | null;
}

export interface TimmsItemDetail {
  item_id: string;
  title: string;
  creator: string | null;
  player_url: string | null;
  citation_downloads: Record<string, string>;
  metadata: TimmsMetadataField[];
  source_url: string | null;
}

export interface TimmsStreamVariant {
  url: string;
  width: number | null;
  height: number | null;
  bitrate: number | null;
  provider: string | null;
  streamer: string | null;
}

export interface TimmsTreeNode {
  node_id: string;
  node_path: string;
  label: string;
  depth: number;
  is_open: boolean;
}

export interface TimmsTreeItem {
  item_id: string;
  title: string;
  url: string;
}

export interface TimmsTreeResponse {
  source_url: string;
  selected_node_id: string | null;
  nodes: TimmsTreeNode[];
  items: TimmsTreeItem[];
}

export interface TalkTag {
  id: number;
  name: string;
  description: string | null;
  total_talks: number | null;
  has_subscribed: boolean | null;
}

export interface Talk {
  id: number;
  title: string;
  timestamp: string;
  description: string | null;
  location: string | null;
  speaker_name: string | null;
  speaker_bio: string | null;
  disabled: boolean;
  source_url: string;
  tags: TalkTag[];
}

export interface TalksResponse {
  scope: string;
  query: string;
  tag_ids: number[];
  total_hits: number;
  returned_hits: number;
  source_url: string;
  items: Talk[];
  available_tags: TalkTag[];
}

export interface CareerFacetOption {
  id: number;
  label: string;
  count: number;
}

export interface CareerPostalCodeOption {
  code: string;
  label: string;
  count: number;
  location: string | null;
}

export interface CareerSubscriptionType {
  id: number;
  title: string;
  short_name: string;
}

export interface CareerSearchFilters {
  project_types: CareerFacetOption[];
  project_subtypes: CareerFacetOption[];
  industries: CareerFacetOption[];
  organizations: CareerFacetOption[];
  postal_codes: CareerPostalCodeOption[];
  subscription_types: CareerSubscriptionType[];
}

export interface CareerProjectSummary {
  id: number;
  title: string;
  preview: string | null;
  location: string | null;
  project_types: string[];
  industries: string[];
  organizations: string[];
  created_at: string | null;
  start_date: string | null;
  end_date: string | null;
  source_url: string;
}

export interface CareerOrganization {
  id: number | null;
  name: string;
  logo_url: string | null;
}

export interface CareerProjectDetail {
  id: number;
  title: string;
  location: string | null;
  description: string | null;
  requirements: string | null;
  project_types: string[];
  industries: string[];
  organizations: CareerOrganization[];
  created_at: string | null;
  start_date: string | null;
  end_date: string | null;
  source_url: string | null;
}

export interface CareerSearchResponse {
  query: string;
  page: number;
  per_page: number;
  total_hits: number;
  total_pages: number;
  source_url: string;
  filters: CareerSearchFilters;
  items: CareerProjectSummary[];
}

export interface CampusMenu {
  id: string;
  menu_line: string | null;
  menu_date: string | null;
  items: string[];
  student_price: string | null;
  guest_price: string | null;
  pupil_price: string | null;
  icons: string[];
  allergens: string[];
  additives: string[];
  co2: string | null;
}

export interface CampusCanteen {
  canteen_id: string;
  canteen: string;
  page_url: string | null;
  address: string | null;
  map_url: string | null;
  menus: CampusMenu[];
}

export interface CampusAreaLink {
  label: string;
  path: string;
  url: string;
}

export interface CampusBuildingSummary {
  title: string;
  path: string;
  url: string;
  area_label: string | null;
}

export interface CampusBuildingDirectory {
  source_url: string;
  area_links: CampusAreaLink[];
  buildings: CampusBuildingSummary[];
}

export interface CampusBuildingDetail {
  title: string;
  subtitle: string | null;
  address_lines: string[];
  building_number: string | null;
  map_label: string | null;
  image_url: string | null;
  marker_title: string | null;
  marker_description: string | null;
  latitude: number | null;
  longitude: number | null;
  source_url: string;
}

export interface KufTrainingOccupancy {
  facility_id: string;
  facility_name: string;
  count: number;
  source_url: string;
  image_url: string;
  retrieved_at: string;
  refresh_after_seconds: number;
}

export interface UniversityCalendarEvent {
  id: string;
  title: string;
  starts_at: string;
  url: string | null;
  speaker: string | null;
  location: string | null;
  description: string | null;
  content_html: string | null;
  categories: string[];
}

export interface UniversityCalendarResponse {
  source_url: string;
  feed_url: string;
  query: string;
  total_hits: number;
  returned_hits: number;
  items: UniversityCalendarEvent[];
}
