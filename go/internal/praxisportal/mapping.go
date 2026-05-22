package praxisportal

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
	"time"
)

func mapSummary(hit map[string]any) (CareerProjectSummary, error) {
	projectID, ok := safeInt(hit["id"])
	if !ok {
		return CareerProjectSummary{}, fmt.Errorf("praxisportal: invalid project id %v", hit["id"])
	}
	projectTypes := namesFromNested(hit["project_type"], "name")
	industries := namesFromNested(hit["industry"], "title")
	organizations := namesFromNested(hit["organization"], "name")

	title := strings.TrimSpace(fmt.Sprintf("%v", hit["title"]))
	createdAt := isoFromTimestamp(hit["created_at"], true)
	startDate := isoFromTimestamp(hit["start_date"], false)
	endDate := isoFromTimestamp(hit["end_date"], false)

	location := cleanText(hit["location"])
	preview := previewFromText(cleanText(hit["job_description"]), 220)

	return CareerProjectSummary{
		ID:            projectID,
		Title:         title,
		Preview:       preview,
		Location:      location,
		ProjectTypes:  projectTypes,
		Industries:    industries,
		Organizations: organizations,
		CreatedAt:     createdAt,
		StartDate:     startDate,
		EndDate:       endDate,
		SourceURL:     fmt.Sprintf("%s/projects/%d", baseURL, projectID),
	}, nil
}

func mapDetail(hit map[string]any) (CareerProjectDetail, error) {
	projectID, ok := safeInt(hit["id"])
	if !ok {
		return CareerProjectDetail{}, fmt.Errorf("praxisportal: invalid project id %v", hit["id"])
	}
	title := strings.TrimSpace(fmt.Sprintf("%v", hit["title"]))

	orgs := mapOrganizations(hit["organization"])

	source := fmt.Sprintf("%s/projects/%d", baseURL, projectID)
	return CareerProjectDetail{
		ID:            projectID,
		Title:         title,
		Location:      cleanText(hit["location"]),
		Description:   cleanText(hit["job_description"]),
		Requirements:  cleanText(hit["requirements"]),
		ProjectTypes:  namesFromNested(hit["project_type"], "name"),
		Industries:    namesFromNested(hit["industry"], "title"),
		Organizations: orgs,
		CreatedAt:     isoFromTimestamp(hit["created_at"], true),
		StartDate:     isoFromTimestamp(hit["start_date"], false),
		EndDate:       isoFromTimestamp(hit["end_date"], false),
		SourceURL:     &source,
	}, nil
}

func buildFacetOptions(counts map[string]int, labels map[int]string) []CareerFacetOption {
	options := make([]CareerFacetOption, 0, len(counts))
	for key, value := range counts {
		id, ok := safeInt(key)
		if !ok {
			continue
		}
		label, ok := labels[id]
		if !ok || strings.TrimSpace(label) == "" {
			continue
		}
		options = append(options, CareerFacetOption{
			ID:    id,
			Label: label,
			Count: value,
		})
	}
	sort.Slice(options, func(i, j int) bool {
		return strings.ToLower(options[i].Label) < strings.ToLower(options[j].Label)
	})
	return options
}

func facetLabelFromHit(facetName string, id int, hit map[string]any) string {
	switch facetName {
	case "project_type.id":
		return nestedLabel(hit["project_type"], id, "id", "name")
	case "industry.id":
		return nestedLabel(hit["industry"], id, "id", "title")
	default:
		return ""
	}
}

func nestedLabel(value any, id int, idKey string, labelKey string) string {
	items := asSlice(value)
	for _, itemAny := range items {
		item, ok := itemAny.(map[string]any)
		if !ok {
			continue
		}
		parsedID, ok := safeInt(item[idKey])
		if !ok || parsedID != id {
			continue
		}
		return strings.TrimSpace(fmt.Sprintf("%v", item[labelKey]))
	}
	return ""
}

func namesFromNested(value any, key string) []string {
	items := asSlice(value)
	names := make([]string, 0, len(items))
	for _, itemAny := range items {
		item, ok := itemAny.(map[string]any)
		if !ok {
			continue
		}
		text := strings.TrimSpace(fmt.Sprintf("%v", item[key]))
		if text == "" {
			continue
		}
		names = append(names, text)
	}
	return names
}

func mapOrganizations(value any) []CareerOrganization {
	items := asSlice(value)
	orgs := make([]CareerOrganization, 0, len(items))
	for _, itemAny := range items {
		item, ok := itemAny.(map[string]any)
		if !ok {
			continue
		}
		name := strings.TrimSpace(fmt.Sprintf("%v", item["name"]))
		if name == "" {
			continue
		}
		var idPtr *int
		if parsedID, ok := safeInt(item["id"]); ok && parsedID > 0 {
			idPtr = &parsedID
		}
		orgs = append(orgs, CareerOrganization{
			ID:      idPtr,
			Name:    name,
			LogoURL: cleanText(item["logo_url"]),
		})
	}
	return orgs
}

func isoFromTimestamp(value any, milliseconds bool) *string {
	if value == nil || value == "" || value == 0 {
		return nil
	}
	var stamp float64
	switch typed := value.(type) {
	case float64:
		stamp = typed
	case float32:
		stamp = float64(typed)
	case int:
		stamp = float64(typed)
	case int64:
		stamp = float64(typed)
	case string:
		parsed, err := strconv.ParseFloat(strings.TrimSpace(typed), 64)
		if err != nil {
			return nil
		}
		stamp = parsed
	default:
		return nil
	}
	if stamp == 0 {
		return nil
	}
	if milliseconds {
		stamp /= 1000
	}
	sec := int64(stamp)
	nsec := int64((stamp - float64(sec)) * 1e9)
	t := time.Unix(sec, nsec).In(berlinLocation())
	formatted := t.Format(time.RFC3339)
	return &formatted
}

func previewFromText(value *string, limit int) *string {
	if value == nil {
		return nil
	}
	cleaned := strings.Join(strings.Fields(*value), " ")
	if cleaned == "" {
		return nil
	}
	if limit <= 0 || len(cleaned) <= limit {
		return &cleaned
	}
	truncated := strings.TrimSpace(cleaned[:limit-1]) + "…"
	return &truncated
}

func cleanText(value any) *string {
	text := strings.TrimSpace(cleanTextValue(value))
	if text == "" {
		return nil
	}
	return &text
}

func cleanTextValue(value any) string {
	if value == nil {
		return ""
	}
	return fmt.Sprintf("%v", value)
}
