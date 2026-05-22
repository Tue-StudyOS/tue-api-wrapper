package talks

import (
	"sort"
	"strings"
)

func BuildResponse(
	talks []Talk,
	scope string,
	query string,
	tagIDs []int,
	includeDisabled bool,
	limit int,
) TalksResponse {
	selectedTags := map[int]struct{}{}
	for _, id := range tagIDs {
		selectedTags[id] = struct{}{}
	}

	visible := make([]Talk, 0, len(talks))
	for _, talk := range talks {
		if includeDisabled || !talk.Disabled {
			visible = append(visible, talk)
		}
	}

	availableTags := buildTagFacets(visible)
	filtered := filterTalks(visible, query, selectedTags)

	if limit <= 0 {
		limit = 24
	}
	if limit > len(filtered) {
		limit = len(filtered)
	}

	return TalksResponse{
		Scope:         scope,
		Query:         query,
		TagIDs:        tagIDs,
		TotalHits:     len(filtered),
		ReturnedHits:  limit,
		SourceURL:     absoluteURL("talks"),
		Items:         filtered[:limit],
		AvailableTags: availableTags,
	}
}

func filterTalks(talks []Talk, query string, selectedTags map[int]struct{}) []Talk {
	normalizedQuery := strings.ToLower(strings.TrimSpace(query))
	filtered := make([]Talk, 0, len(talks))

	for _, talk := range talks {
		if len(selectedTags) > 0 && disjoint(selectedTags, talk.Tags) {
			continue
		}
		if normalizedQuery != "" {
			haystack := strings.ToLower(strings.Join([]string{
				talk.Title,
				stringOrEmpty(talk.Description),
				stringOrEmpty(talk.Location),
				stringOrEmpty(talk.SpeakerName),
				stringOrEmpty(talk.SpeakerBio),
				tagNames(talk.Tags),
			}, "\n"))
			if !strings.Contains(haystack, normalizedQuery) {
				continue
			}
		}
		filtered = append(filtered, talk)
	}
	return filtered
}

func disjoint(selected map[int]struct{}, tags []TalkTag) bool {
	for _, tag := range tags {
		if _, ok := selected[tag.ID]; ok {
			return false
		}
	}
	return true
}

func tagNames(tags []TalkTag) string {
	values := make([]string, 0, len(tags))
	for _, tag := range tags {
		values = append(values, tag.Name)
	}
	return strings.Join(values, " ")
}

func stringOrEmpty(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

func buildTagFacets(talks []Talk) []TalkTag {
	names := map[int]string{}
	counts := map[int]int{}
	for _, talk := range talks {
		for _, tag := range talk.Tags {
			names[tag.ID] = tag.Name
			counts[tag.ID]++
		}
	}

	ids := make([]int, 0, len(counts))
	for id := range counts {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool {
		return strings.ToLower(names[ids[i]]) < strings.ToLower(names[ids[j]])
	})

	available := make([]TalkTag, 0, len(ids))
	for _, id := range ids {
		count := counts[id]
		available = append(available, TalkTag{
			ID:         id,
			Name:       names[id],
			TotalTalks: &count,
		})
	}
	return available
}
