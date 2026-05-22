package praxisportal

type CareerFacetOption struct {
	ID    int    `json:"id"`
	Label string `json:"label"`
	Count int    `json:"count"`
}

type CareerSearchFilters struct {
	ProjectTypes []CareerFacetOption `json:"project_types"`
	Industries   []CareerFacetOption `json:"industries"`
}

type CareerOrganization struct {
	ID      *int    `json:"id"`
	Name    string  `json:"name"`
	LogoURL *string `json:"logo_url"`
}

type CareerProjectSummary struct {
	ID            int      `json:"id"`
	Title         string   `json:"title"`
	Preview       *string  `json:"preview"`
	Location      *string  `json:"location"`
	ProjectTypes  []string `json:"project_types"`
	Industries    []string `json:"industries"`
	Organizations []string `json:"organizations"`
	CreatedAt     *string  `json:"created_at"`
	StartDate     *string  `json:"start_date"`
	EndDate       *string  `json:"end_date"`
	SourceURL     string   `json:"source_url"`
}

type CareerProjectDetail struct {
	ID            int                  `json:"id"`
	Title         string               `json:"title"`
	Location      *string              `json:"location"`
	Description   *string              `json:"description"`
	Requirements  *string              `json:"requirements"`
	ProjectTypes  []string             `json:"project_types"`
	Industries    []string             `json:"industries"`
	Organizations []CareerOrganization `json:"organizations"`
	CreatedAt     *string              `json:"created_at"`
	StartDate     *string              `json:"start_date"`
	EndDate       *string              `json:"end_date"`
	SourceURL     *string              `json:"source_url"`
}

type CareerSearchResponse struct {
	Query      string                 `json:"query"`
	Page       int                    `json:"page"`
	PerPage    int                    `json:"per_page"`
	TotalHits  int                    `json:"total_hits"`
	TotalPages int                    `json:"total_pages"`
	SourceURL  string                 `json:"source_url"`
	Filters    CareerSearchFilters    `json:"filters"`
	Items      []CareerProjectSummary `json:"items"`
}
