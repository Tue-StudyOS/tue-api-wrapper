package praxisportal

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

const (
	baseURL          = "https://www.praxisportal.uni-tuebingen.de"
	algoliaAppID     = "ESD35NPPR9"
	algoliaAPIKey    = "fc3088fb6da3aa814eb902f0635f46b3"
	algoliaIndex     = "projects_prd"
	algoliaNewestIdx = "projects_prd_newest"
)

type Client struct {
	http *http.Client
}

func New(timeout time.Duration) *Client {
	return &Client{http: &http.Client{Timeout: timeout}}
}

func (c *Client) SearchProjects(query string, projectTypeIDs []int, industryIDs []int, page int, perPage int, sort string) (*CareerSearchResponse, error) {
	loc := berlinLocation()
	visibility := buildVisibilityFilter(time.Now().In(loc))
	filterExpr := buildFilterExpression(visibility, projectTypeIDs, industryIDs)

	if perPage <= 0 {
		perPage = 20
	}
	if page < 0 {
		page = 0
	}
	index := algoliaNewestIdx
	if strings.TrimSpace(sort) != "" && strings.TrimSpace(sort) != "newest" {
		index = algoliaIndex
	}

	params := map[string]any{
		"query":         query,
		"optionalWords": query,
		"filters":       filterExpr,
		"hitsPerPage":   perPage,
		"page":          page,
		"facets":        []string{"project_type.id", "industry.id"},
	}
	paramsStr := buildAlgoliaParams(params, "[]:,()<> ")

	payload, err := c.algoliaPost(fmt.Sprintf("/1/indexes/%s/query", index), map[string]any{"params": paramsStr})
	if err != nil {
		return nil, err
	}

	filters, err := c.FetchFilterOptions()
	if err != nil {
		return nil, err
	}

	hits := asSlice(payload["hits"])
	items := make([]CareerProjectSummary, 0, len(hits))
	for _, hitAny := range hits {
		hit, ok := hitAny.(map[string]any)
		if !ok {
			continue
		}
		summary, err := mapSummary(hit)
		if err != nil {
			return nil, err
		}
		items = append(items, summary)
	}

	resp := &CareerSearchResponse{
		Query:      query,
		Page:       intOr(payload["page"], page),
		PerPage:    intOr(payload["hitsPerPage"], perPage),
		TotalHits:  intOr(payload["nbHits"], 0),
		TotalPages: intOr(payload["nbPages"], 0),
		SourceURL:  baseURL + "/candidate/search",
		Filters:    *filters,
		Items:      items,
	}
	return resp, nil
}

func (c *Client) FetchProject(projectID int) (*CareerProjectDetail, error) {
	objectID := quote(fmt.Sprintf("App\\Models\\Project::%d", projectID), "")
	payload, err := c.algoliaGet(fmt.Sprintf("/1/indexes/%s/%s", algoliaIndex, objectID))
	if err != nil {
		return nil, err
	}
	detail, err := mapDetail(payload)
	if err != nil {
		return nil, err
	}
	return &detail, nil
}

func (c *Client) FetchFilterOptions() (*CareerSearchFilters, error) {
	loc := berlinLocation()
	visibility := buildVisibilityFilter(time.Now().In(loc))
	visibilityEscaped := quote(visibility, "()<>:= ")

	payload, err := c.algoliaPost(
		fmt.Sprintf("/1/indexes/%s/query", algoliaIndex),
		map[string]any{"params": "query=&hitsPerPage=0&facets=" + quote(`["project_type.id","industry.id"]`, "[]\",") + "&filters=" + visibilityEscaped},
	)
	if err != nil {
		return nil, err
	}

	facets, _ := payload["facets"].(map[string]any)
	projectTypeCounts := asStringIntMap(facets["project_type.id"])
	industryCounts := asStringIntMap(facets["industry.id"])

	projectTypeIDs := keysAsInts(projectTypeCounts)
	industryIDs := keysAsInts(industryCounts)

	projectTypeLabels, err := c.facetLabels(visibility, "project_type.id", projectTypeIDs)
	if err != nil {
		return nil, err
	}
	industryLabels, err := c.facetLabels(visibility, "industry.id", industryIDs)
	if err != nil {
		return nil, err
	}

	return &CareerSearchFilters{
		ProjectTypes: buildFacetOptions(projectTypeCounts, projectTypeLabels),
		Industries:   buildFacetOptions(industryCounts, industryLabels),
	}, nil
}

func (c *Client) facetLabels(visibility string, facetName string, ids []int) (map[int]string, error) {
	requests := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		filter := visibility + " AND " + facetName + ":" + strconv.Itoa(id)
		requests = append(requests, map[string]any{
			"indexName": algoliaIndex,
			"params":    "query=&hitsPerPage=1&filters=" + quote(filter, "()<>:= "),
		})
	}

	payload, err := c.algoliaPost("/1/indexes/*/queries", map[string]any{"requests": requests})
	if err != nil {
		return nil, err
	}
	results := asSlice(payload["results"])
	labels := map[int]string{}
	for idx, resultAny := range results {
		if idx >= len(ids) {
			break
		}
		result, ok := resultAny.(map[string]any)
		if !ok {
			continue
		}
		hits := asSlice(result["hits"])
		if len(hits) == 0 {
			continue
		}
		hit, ok := hits[0].(map[string]any)
		if !ok {
			continue
		}
		label := facetLabelFromHit(facetName, ids[idx], hit)
		if label != "" {
			labels[ids[idx]] = label
		}
	}
	return labels, nil
}

func (c *Client) algoliaPost(path string, payload any) (map[string]any, error) {
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest(http.MethodPost, algoliaBaseURL()+path, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Algolia-Application-Id", algoliaAppID)
	req.Header.Set("X-Algolia-API-Key", algoliaAPIKey)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("praxisportal request failed with HTTP %d", resp.StatusCode)
	}

	var decoded map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		return nil, err
	}
	return decoded, nil
}

func (c *Client) algoliaGet(path string) (map[string]any, error) {
	req, err := http.NewRequest(http.MethodGet, algoliaBaseURL()+path, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Algolia-Application-Id", algoliaAppID)
	req.Header.Set("X-Algolia-API-Key", algoliaAPIKey)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("praxisportal request failed with HTTP %d", resp.StatusCode)
	}

	var decoded map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		return nil, err
	}
	return decoded, nil
}

func algoliaBaseURL() string {
	return fmt.Sprintf("https://%s-dsn.algolia.net", algoliaAppID)
}
