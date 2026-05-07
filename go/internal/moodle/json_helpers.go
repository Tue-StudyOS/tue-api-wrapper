package moodle

import (
	"net/url"
)

func asItems(payload any) []map[string]any {
	switch value := payload.(type) {
	case []any:
		return anyListToMaps(value)
	case map[string]any:
		for _, key := range []string{"events", "courses", "items"} {
			if items, ok := value[key].([]any); ok {
				return anyListToMaps(items)
			}
		}
		return []map[string]any{value}
	default:
		return nil
	}
}

func anyListToMaps(values []any) []map[string]any {
	items := []map[string]any{}
	for _, item := range values {
		if mapped, ok := item.(map[string]any); ok {
			items = append(items, mapped)
		}
	}
	return items
}

func nextOffset(payload any) *int {
	mapped, ok := payload.(map[string]any)
	if !ok {
		return nil
	}
	for _, key := range []string{"nextoffset", "next_offset"} {
		switch value := mapped[key].(type) {
		case float64:
			return intPtr(int(value))
		case int:
			return intPtr(value)
		}
	}
	return nil
}

func cloneMapValues(source map[string]string) url.Values {
	values := url.Values{}
	for key, value := range source {
		values.Set(key, value)
	}
	return values
}

func valueInt(value *int) int {
	if value == nil {
		return 0
	}
	return *value
}
