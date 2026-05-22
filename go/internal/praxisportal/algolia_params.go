package praxisportal

import (
	"encoding/json"
	"fmt"
	"sort"
	"strconv"
	"strings"
)

func buildAlgoliaParams(params map[string]any, safe string) string {
	keys := make([]string, 0, len(params))
	for key := range params {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	items := make([]string, 0, len(keys))
	for _, key := range keys {
		value := params[key]
		if value == nil {
			continue
		}
		str, ok := stringifyAlgoliaValue(value)
		if !ok || strings.TrimSpace(str) == "" {
			continue
		}
		items = append(items, key+"="+quote(str, safe))
	}
	return strings.Join(items, "&")
}

func stringifyAlgoliaValue(value any) (string, bool) {
	switch typed := value.(type) {
	case string:
		return typed, true
	case []string:
		encoded, err := json.Marshal(typed)
		if err != nil {
			return "", false
		}
		return string(encoded), true
	case []any, map[string]any, map[string]string:
		encoded, err := json.Marshal(typed)
		if err != nil {
			return "", false
		}
		return string(encoded), true
	case bool:
		if typed {
			return "true", true
		}
		return "false", true
	case int:
		return strconv.Itoa(typed), true
	case int64:
		return strconv.FormatInt(typed, 10), true
	case float64:
		if typed == float64(int64(typed)) {
			return strconv.FormatInt(int64(typed), 10), true
		}
		return fmt.Sprintf("%v", typed), true
	default:
		encoded, err := json.Marshal(value)
		if err != nil {
			return "", false
		}
		return string(encoded), true
	}
}
