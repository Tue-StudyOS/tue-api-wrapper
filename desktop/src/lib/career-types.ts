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
