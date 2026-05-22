package seatfinder

import (
	"encoding/json"
	"fmt"
	"math"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

var jsonpWrapper = regexp.MustCompile(`(?s)^[\\w$]+\\s*\\((.*)\\)\\s*;?\\s*$`)

func parsePayload(text string) (any, error) {
	stripped := strings.TrimSpace(text)
	if match := jsonpWrapper.FindStringSubmatch(stripped); match != nil {
		stripped = match[1]
	}
	var decoded any
	if err := json.Unmarshal([]byte(stripped), &decoded); err != nil {
		return nil, err
	}
	return decoded, nil
}

func ParseAvailabilityPayload(payload any, sourceURL string, retrievedAt string) (*SeatAvailabilityResponse, error) {
	items, ok := payload.([]any)
	if !ok {
		return nil, fmt.Errorf("seatfinder response was not a list")
	}

	counts := firstMapping(items, "seatestimate")
	locations := firstMapping(items, "location")

	ids := make([]string, 0, len(locations))
	for id := range locations {
		ids = append(ids, id)
	}
	sort.Strings(ids)

	statuses := make([]SeatLocationStatus, 0, len(ids))
	for _, id := range ids {
		locationRows := locations[id]
		estimateRows := counts[id]
		status := buildLocationStatus(id, locationRows, estimateRows)
		if status != nil {
			statuses = append(statuses, *status)
		}
	}

	return &SeatAvailabilityResponse{
		SourceURL:   sourceURL,
		RetrievedAt: retrievedAt,
		Locations:   statuses,
	}, nil
}

func firstMapping(payload []any, key string) map[string][]map[string]any {
	for _, item := range payload {
		entry, ok := item.(map[string]any)
		if !ok {
			continue
		}
		raw, ok := entry[key].(map[string]any)
		if !ok {
			continue
		}
		out := map[string][]map[string]any{}
		for locationID, rowsAny := range raw {
			rowsSlice, ok := rowsAny.([]any)
			if !ok {
				continue
			}
			rows := make([]map[string]any, 0, len(rowsSlice))
			for _, rowAny := range rowsSlice {
				row, ok := rowAny.(map[string]any)
				if !ok {
					continue
				}
				rows = append(rows, row)
			}
			out[fmt.Sprintf("%v", locationID)] = rows
		}
		return out
	}
	return map[string][]map[string]any{}
}

func buildLocationStatus(locationID string, locationRows []map[string]any, estimateRows []map[string]any) *SeatLocationStatus {
	location := latestRow(locationRows)
	if location == nil {
		return nil
	}
	estimate := latestRow(estimateRows)
	if estimate == nil {
		estimate = map[string]any{}
	}

	totalSeats := intOrNil(location["available_seats"])
	freeSeats := intOrNil(estimate["free_seats"])
	occupiedSeats := intOrNil(estimate["occupied_seats"])
	if totalSeats == nil && freeSeats != nil && occupiedSeats != nil {
		sum := *freeSeats + *occupiedSeats
		totalSeats = &sum
	}

	return &SeatLocationStatus{
		LocationID:       locationID,
		Name:             textOr(location["name"], locationID),
		LongName:         textOrNil(location["long_name"]),
		Level:            textOrNil(location["level"]),
		Building:         textOrNil(location["building"]),
		Room:             textOrNil(location["room"]),
		TotalSeats:       totalSeats,
		FreeSeats:        freeSeats,
		OccupiedSeats:    occupiedSeats,
		OccupancyPercent: occupancyPercent(occupiedSeats, totalSeats),
		UpdatedAt:        timestampText(firstNonNil(estimate["timestamp"], location["timestamp"])),
		URL:              textOrNil(location["url"]),
		GeoCoordinates:   textOrNil(location["geo_coordinates"]),
	}
}

func latestRow(rows []map[string]any) map[string]any {
	var latest map[string]any
	var latestKey string
	for _, row := range rows {
		key := ""
		if stamp := timestampText(row["timestamp"]); stamp != nil {
			key = *stamp
		}
		if latest == nil || key > latestKey {
			latest = row
			latestKey = key
		}
	}
	return latest
}

func timestampText(value any) *string {
	switch typed := value.(type) {
	case map[string]any:
		raw := strings.TrimSpace(fmt.Sprintf("%v", typed["date"]))
		if raw == "" {
			return nil
		}
		loc := germanLocation()
		if parsed, err := time.ParseInLocation("2006-01-02 15:04:05.000000", raw, loc); err == nil {
			formatted := parsed.In(loc).Format(time.RFC3339)
			return &formatted
		}
		return &raw
	default:
		return textOrNil(value)
	}
}

func occupancyPercent(occupied *int, total *int) *float64 {
	if occupied == nil || total == nil || *total == 0 {
		return nil
	}
	value := (float64(*occupied) / float64(*total)) * 100
	rounded := math.Round(value*10) / 10
	return &rounded
}

func intOrNil(value any) *int {
	parsed, ok := safeInt(value)
	if !ok {
		return nil
	}
	return &parsed
}

func safeInt(value any) (int, bool) {
	switch typed := value.(type) {
	case float64:
		return int(typed), true
	case int:
		return typed, true
	case string:
		parsed, err := strconv.Atoi(strings.TrimSpace(typed))
		if err != nil {
			return 0, false
		}
		return parsed, true
	default:
		return 0, false
	}
}

func textOrNil(value any) *string {
	if value == nil {
		return nil
	}
	text := strings.TrimSpace(fmt.Sprintf("%v", value))
	if text == "" {
		return nil
	}
	return &text
}

func textOr(value any, fallback string) string {
	if text := textOrNil(value); text != nil {
		return *text
	}
	return fallback
}

func firstNonNil(values ...any) any {
	for _, value := range values {
		if value != nil {
			return value
		}
	}
	return nil
}
