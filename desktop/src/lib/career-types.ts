export interface CareerFacetOption {
  id: number;
  label: string;
  count: number;
}

export interface CareerSearchFilters {
  project_types: CareerFacetOption[];
  industries: CareerFacetOption[];
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
